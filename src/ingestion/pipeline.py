import os
import json
import glob
import logging
from datetime import datetime
from typing import List, Tuple
from pydantic import ValidationError

from src.ingestion.parsers import get_parser
from src.ingestion.normalizer import normalize_row
from src.ingestion.resolver import resolve_entities
from src.core.schemas import PlayerRecord

logger = logging.getLogger(__name__)

def load_and_parse_files(raw_dir: str) -> Tuple[List[dict], List[dict]]:
    """
    Reads all .html and .rtf files in raw_dir.
    Returns (valid_raw_rows, parse_errors)
    """
    all_raw_rows = []
    parse_errors = []
    
    html_files = glob.glob(os.path.join(raw_dir, "*.html")) + glob.glob(os.path.join(raw_dir, "*.htm"))
    rtf_files = glob.glob(os.path.join(raw_dir, "*.rtf"))
    
    all_files = html_files + rtf_files
    
    for filepath in all_files:
        try:
            parser = get_parser(filepath)
            rows = parser.parse(filepath)
            all_raw_rows.extend(rows)
        except Exception as e:
            logger.error(f"Failed to parse file {filepath}: {e}")
            parse_errors.append({"file": filepath, "error": str(e)})
            
    return all_raw_rows, parse_errors

def process_pipeline(raw_dir: str, processed_dir: str, batch_id: str = None):
    """
    End-to-end ingestion pipeline:
    1. Parse files
    2. Normalize and validate schema
    3. Resolve entities (deduplicate)
    4. Save output atomically
    """
    if not batch_id:
        batch_id = datetime.now().strftime("%Y-%m-%d")
        
    os.makedirs(processed_dir, exist_ok=True)
    
    raw_rows, parse_errors = load_and_parse_files(raw_dir)
    
    valid_records = []
    rejected_rows = []
    
    for row in raw_rows:
        try:
            normalized = normalize_row(row)
            record = PlayerRecord(**normalized)
            valid_records.append(record)
        except ValidationError as e:
            rejected_rows.append({
                "raw_data": row,
                "error": e.errors()
            })
        except Exception as e:
            rejected_rows.append({
                "raw_data": row,
                "error": str(e)
            })
            
    # Resolve entities
    resolved_records = resolve_entities(valid_records)
    
    # Save successful records (could be Parquet, using JSON lines for simplicity right now)
    output_file = os.path.join(processed_dir, f"export_{batch_id}.jsonl")
    temp_file_path = output_file + ".tmp"
    try:
        with open(temp_file_path, "w", encoding="utf-8") as f:
            for record in resolved_records:
                f.write(record.model_dump_json() + "\n")
        # Operasi rename di OS umumnya bersifat atomic
        os.replace(temp_file_path, output_file) 
    except Exception as e:
        logger.error(f"Gagal menulis batch_id {batch_id}: {e}")
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
            
    # Save rejected rows (Dead letter log)
    if rejected_rows:
        rejected_file = os.path.join(processed_dir, f"rejected_rows_{batch_id}.json")
        temp_rej_path = rejected_file + ".tmp"
        try:
            with open(temp_rej_path, "w", encoding="utf-8") as f:
                json.dump(rejected_rows, f, indent=2, ensure_ascii=False)
            os.replace(temp_rej_path, rejected_file)
        except Exception as e:
            logger.error(f"Gagal menulis rejected rows {batch_id}: {e}")
            if os.path.exists(temp_rej_path):
                os.remove(temp_rej_path)
            
    return {
        "status": "success",
        "batch_id": batch_id,
        "files_processed": len(raw_rows),
        "valid_records": len(valid_records),
        "resolved_records": len(resolved_records),
        "rejected_rows": len(rejected_rows),
        "parse_errors": parse_errors
    }
