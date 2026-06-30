import os
from abc import ABC, abstractmethod
from bs4 import BeautifulSoup
from striprtf.striprtf import rtf_to_text
from typing import List, Dict, Any

class BaseParser(ABC):
    @abstractmethod
    def parse(self, filepath: str) -> List[Dict[str, Any]]:
        pass

class HTMLParser(BaseParser):
    def parse(self, filepath: str) -> List[Dict[str, Any]]:
        with open(filepath, "r", encoding="utf-8") as f:
            soup = BeautifulSoup(f, "html.parser")
            
        tables = soup.find_all("table")
        if not tables:
            return []
            
        # Assuming the first table is the main data table
        table = tables[0]
        
        # Extract headers
        headers = []
        thead = table.find("thead")
        if thead:
            header_rows = thead.find_all("tr")
            if header_rows:
                # Sometimes there are multiple header rows, take the last one
                th_elements = header_rows[-1].find_all("th")
                headers = [th.get_text(strip=True) for th in th_elements]
        else:
            # Fallback if no thead
            tr = table.find("tr")
            if tr:
                th_elements = tr.find_all(["th", "td"])
                headers = [th.get_text(strip=True) for th in th_elements]
                
        # Extract rows
        data = []
        tbody = table.find("tbody")
        rows = tbody.find_all("tr") if tbody else table.find_all("tr")[1:]
        
        for row in rows:
            tds = row.find_all("td")
            if len(tds) != len(headers):
                continue  # Skip malformed rows
                
            row_data = {}
            for header, td in zip(headers, tds):
                # Handle empty strings and replace them with None/empty
                val = td.get_text(strip=True)
                row_data[header] = val if val else None
            data.append(row_data)
            
        return data

class RTFParser(BaseParser):
    def parse(self, filepath: str) -> List[Dict[str, Any]]:
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            raw_content = f.read()
            
        if "| Name" in raw_content or "|  Name" in raw_content:
            # FM24 exports plain text tables but names them .rtf
            text = raw_content
        else:
            text = rtf_to_text(raw_content)
            
        lines = text.split("\n")
        
        # Find table start (lines starting with | or containing multiple |)
        table_lines = [line.strip() for line in lines if "|" in line]
        
        if not table_lines:
            return []
            
        # The first table line is usually the header
        header_line = table_lines[0]
        # Split by | and filter out empty strings at the edges
        headers = [h.strip() for h in header_line.split("|")[1:-1]]
        
        data = []
        for line in table_lines[1:]:
            # Skip separator lines like |---|---|
            if line.replace("|", "").replace("-", "").strip() == "":
                continue
                
            cells = [c.strip() for c in line.split("|")[1:-1]]
            
            # Pad or truncate cells to match headers
            if len(cells) < len(headers):
                cells.extend([None] * (len(headers) - len(cells)))
            elif len(cells) > len(headers):
                cells = cells[:len(headers)]
                
            row_data = {}
            for header, cell in zip(headers, cells):
                row_data[header] = cell if cell else None
            data.append(row_data)
            
        return data

def get_parser(filepath: str) -> BaseParser:
    ext = os.path.splitext(filepath)[1].lower()
    if ext in [".html", ".htm"]:
        return HTMLParser()
    elif ext == ".rtf":
        return RTFParser()
    else:
        raise ValueError(f"Unsupported file extension: {ext}")
