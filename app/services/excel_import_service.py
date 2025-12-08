"""
Excel Import Service for kasa.xlsx
Imports transaction data from Excel files
"""
import pandas as pd
import logging
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from typing import Dict, List, Tuple, Any, Optional
from app import db
from app.models.transaction import Transaction

logger = logging.getLogger(__name__)

class ExcelImportService:
    """Service for importing transactions from Excel files"""
    
    # Kategori mapping: Excel → Database
    CATEGORY_MAPPING = {
        'YATIRIM': 'DEP',
        'ÇEKME': 'WD',
        'Investment': 'DEP',
        'Withdrawal': 'WD',
        'Deposit': 'DEP'
    }
    
    # Daily USD exchange rates (KUR) from KASA.xlsx
    # Format: 'YYYY-MM-DD': Decimal(rate)
    DAILY_KUR_RATES = {
        # HAZİRAN 2025
        '2025-06-01': Decimal('39.25'),
        '2025-06-02': Decimal('39.25'),
        '2025-06-03': Decimal('39.25'),
        '2025-06-04': Decimal('39.25'),
        '2025-06-05': Decimal('39.25'),
        '2025-06-06': Decimal('39.25'),
        '2025-06-07': Decimal('39.25'),
        '2025-06-08': Decimal('39.25'),
        '2025-06-09': Decimal('39.25'),
        '2025-06-10': Decimal('39.25'),
        '2025-06-11': Decimal('39.33'),
        '2025-06-12': Decimal('39.33'),
        '2025-06-13': Decimal('39.33'),
        '2025-06-14': Decimal('39.33'),
        '2025-06-15': Decimal('39.33'),
        '2025-06-16': Decimal('39.33'),
        '2025-06-17': Decimal('39.50'),
        '2025-06-18': Decimal('39.50'),
        '2025-06-19': Decimal('39.50'),
        '2025-06-20': Decimal('39.50'),
        '2025-06-21': Decimal('39.50'),
        '2025-06-22': Decimal('39.70'),
        '2025-06-23': Decimal('39.70'),
        '2025-06-24': Decimal('39.70'),
        '2025-06-25': Decimal('39.70'),
        '2025-06-26': Decimal('39.85'),
        '2025-06-27': Decimal('39.85'),
        '2025-06-28': Decimal('39.85'),
        '2025-06-29': Decimal('39.85'),
        '2025-06-30': Decimal('39.85'),
        # TEMMUZ 2025
        '2025-07-01': Decimal('39.85'),
        '2025-07-02': Decimal('39.85'),
        '2025-07-03': Decimal('39.85'),
        '2025-07-04': Decimal('39.85'),
        '2025-07-05': Decimal('39.85'),
        '2025-07-06': Decimal('40.00'),
        '2025-07-07': Decimal('40.00'),
        '2025-07-08': Decimal('40.00'),
        '2025-07-09': Decimal('40.00'),
        '2025-07-10': Decimal('40.00'),
        '2025-07-11': Decimal('40.00'),
        '2025-07-12': Decimal('40.00'),
        '2025-07-13': Decimal('40.00'),
        '2025-07-14': Decimal('40.00'),
        '2025-07-15': Decimal('40.00'),
        '2025-07-16': Decimal('40.00'),
        '2025-07-17': Decimal('40.20'),
        '2025-07-18': Decimal('40.20'),
        '2025-07-19': Decimal('40.20'),
        '2025-07-20': Decimal('40.20'),
        '2025-07-21': Decimal('40.20'),
        '2025-07-22': Decimal('40.60'),
        '2025-07-23': Decimal('40.60'),
        '2025-07-24': Decimal('40.60'),
        '2025-07-25': Decimal('40.60'),
        '2025-07-26': Decimal('40.60'),
        '2025-07-27': Decimal('40.60'),
        '2025-07-28': Decimal('40.60'),
        '2025-07-29': Decimal('40.60'),
        '2025-07-30': Decimal('40.60'),
        '2025-07-31': Decimal('40.60'),
        # AĞUSTOS 2025
        '2025-08-01': Decimal('40.60'),
        '2025-08-02': Decimal('40.60'),
        '2025-08-03': Decimal('40.60'),
        '2025-08-04': Decimal('40.60'),
        '2025-08-05': Decimal('40.60'),
        '2025-08-06': Decimal('40.60'),
        '2025-08-07': Decimal('40.60'),
        '2025-08-08': Decimal('40.60'),
        '2025-08-09': Decimal('40.60'),
        '2025-08-10': Decimal('40.60'),
        '2025-08-11': Decimal('40.60'),
        '2025-08-12': Decimal('40.60'),
        '2025-08-13': Decimal('40.60'),
        '2025-08-14': Decimal('40.60'),
        '2025-08-15': Decimal('40.60'),
        '2025-08-16': Decimal('40.90'),
        '2025-08-17': Decimal('40.90'),
        '2025-08-18': Decimal('40.90'),
        '2025-08-19': Decimal('40.90'),
        '2025-08-20': Decimal('40.90'),
        '2025-08-21': Decimal('40.90'),
        '2025-08-22': Decimal('41.00'),
        '2025-08-23': Decimal('41.00'),
        '2025-08-24': Decimal('41.00'),
        '2025-08-25': Decimal('41.00'),
        '2025-08-26': Decimal('41.00'),
        '2025-08-27': Decimal('41.00'),
        '2025-08-28': Decimal('41.00'),
        '2025-08-29': Decimal('41.00'),
        '2025-08-30': Decimal('41.00'),
        '2025-08-31': Decimal('41.00'),
        # EYLÜL 2025
        '2025-09-01': Decimal('41.20'),
        '2025-09-02': Decimal('41.20'),
        '2025-09-03': Decimal('41.20'),
        '2025-09-04': Decimal('41.20'),
        '2025-09-05': Decimal('41.20'),
        '2025-09-06': Decimal('41.20'),
        '2025-09-08': Decimal('41.20'),
        '2025-09-09': Decimal('41.20'),
        '2025-09-10': Decimal('41.20'),
        '2025-09-11': Decimal('41.20'),
        '2025-09-12': Decimal('41.20'),
        '2025-09-13': Decimal('41.20'),
        '2025-09-14': Decimal('41.20'),
        '2025-09-15': Decimal('41.20'),
        '2025-09-16': Decimal('41.50'),
        '2025-09-17': Decimal('41.50'),
        '2025-09-18': Decimal('41.70'),
        '2025-09-19': Decimal('41.70'),
        '2025-09-20': Decimal('41.70'),
        '2025-09-21': Decimal('41.70'),
        '2025-09-22': Decimal('41.70'),
        '2025-09-23': Decimal('41.70'),
        '2025-09-24': Decimal('41.70'),
        '2025-09-25': Decimal('41.70'),
        '2025-09-26': Decimal('41.70'),
        '2025-09-27': Decimal('41.70'),
        '2025-09-28': Decimal('41.70'),
        '2025-09-29': Decimal('41.70'),
        '2025-09-30': Decimal('41.70'),
        # EKİM 2025
        '2025-10-01': Decimal('41.70'),
        '2025-10-02': Decimal('41.70'),
        '2025-10-03': Decimal('41.70'),
        '2025-10-04': Decimal('41.70'),
        '2025-10-05': Decimal('41.70'),
        '2025-10-06': Decimal('41.70'),
        '2025-10-07': Decimal('41.70'),
        '2025-10-08': Decimal('41.70'),
        '2025-10-09': Decimal('41.70'),
        '2025-10-10': Decimal('41.70'),
        '2025-10-11': Decimal('41.70'),
        '2025-10-12': Decimal('41.70'),
        '2025-10-13': Decimal('42.00'),
        '2025-10-14': Decimal('42.00'),
        '2025-10-15': Decimal('42.00'),
        '2025-10-16': Decimal('42.00'),
        '2025-10-17': Decimal('42.00'),
        '2025-10-18': Decimal('42.00'),
        '2025-10-19': Decimal('42.00'),
        '2025-10-20': Decimal('42.00'),
        '2025-10-21': Decimal('42.00'),
        '2025-10-22': Decimal('42.05'),
        '2025-10-23': Decimal('42.05'),
        '2025-10-24': Decimal('42.05'),
        '2025-10-25': Decimal('42.05'),
        '2025-10-26': Decimal('42.05'),
        '2025-10-27': Decimal('42.05'),
        '2025-10-28': Decimal('42.05'),
        '2025-10-29': Decimal('42.05'),
        '2025-10-30': Decimal('42.05'),
        '2025-10-31': Decimal('42.05'),
        # KASIM 2025
        '2025-11-01': Decimal('42.20'),
        '2025-11-02': Decimal('42.20'),
        '2025-11-03': Decimal('42.20'),
        '2025-11-04': Decimal('42.20'),
        '2025-11-05': Decimal('42.20'),
        '2025-11-06': Decimal('42.20'),
        '2025-11-07': Decimal('42.20'),
        '2025-11-08': Decimal('42.20'),
        '2025-11-09': Decimal('42.20'),
        '2025-11-10': Decimal('42.20'),
        '2025-11-11': Decimal('42.20'),
        '2025-11-12': Decimal('42.20'),
        '2025-11-13': Decimal('42.20'),
        '2025-11-14': Decimal('42.60'),
        '2025-11-15': Decimal('42.60'),
        '2025-11-16': Decimal('42.60'),
        '2025-11-17': Decimal('42.60'),
        '2025-11-18': Decimal('42.60'),
        '2025-11-19': Decimal('42.60'),
        '2025-11-20': Decimal('42.60'),
        '2025-11-21': Decimal('42.60'),
        '2025-11-22': Decimal('42.60'),
        '2025-11-23': Decimal('42.60'),
        '2025-11-24': Decimal('42.60'),
        '2025-11-25': Decimal('42.60'),
        '2025-11-26': Decimal('42.60'),
        '2025-11-27': Decimal('42.60'),
        '2025-11-28': Decimal('42.60'),
        '2025-11-29': Decimal('42.60'),
        '2025-11-30': Decimal('42.60'),
    }
    
    # Para birimi normalizasyonu
    CURRENCY_MAPPING = {
        'TL': 'TL',
        'TRY': 'TL',
        'USD': 'USD',
        'DOLAR': 'USD',
        'DOLLAR': 'USD',
        'EUR': 'EUR',
        'EURO': 'EUR'
    }
    
    # Sheet yapıları - her sheet için kolon mapping
    SHEET_CONFIGS = {
        'HAZİRAN': {
            'header_row': 1,
            'cols': {
                'client': 0,
                'iban': 1,  # Kullanılmayacak
                'payment': 2,
                'psp': 3,  # FIXED: Column 3 contains PSP, not company
                'date': 4,
                'category': 5,
                'amount': 6,
                'commission': 7,
                'net': 8,
                'currency': 9,
                'company': 10,  # FIXED: Column 10 contains Company, not PSP
                'kur': 18  # KUR değeri bu kolonda
            }
        },
        'TEMMUZ': {
            'header_row': 1,
            'cols': {
                'client': 2,
                'iban': 3,  # Kullanılmayacak
                'payment': 4,
                'psp': 5,  # FIXED: Column 5 contains PSP, not company
                'date': 6,
                'category': 7,
                'amount': 8,
                'commission': 9,
                'net': 10,
                'currency': 11,
                'company': 12,  # FIXED: Column 12 contains Company, not PSP
                'kur': 20  # KUR kolonu
            }
        },
        'AĞUSTOS': {
            'header_row': 1,
            'cols': {
                'client': 2,
                'iban': 3,  # Kullanılmayacak
                'payment': 4,
                'psp': 5,  # FIXED: Column 5 contains PSP, not company
                'date': 6,
                'category': 7,
                'amount': 8,
                'commission': 9,
                'net': 10,
                'currency': 11,
                'company': 12,  # FIXED: Column 12 contains Company, not PSP
                'kur': 20  # KUR kolonu
            }
        },
        'EYLÜL': {
            'header_row': 1,
            'cols': {
                'client': 2,
                'iban': 3,  # Kullanılmayacak
                'payment': 4,
                'psp': 5,  # FIXED: Column 5 contains PSP, not company
                'date': 6,
                'category': 7,
                'amount': 8,
                'commission': 9,
                'net': 10,
                'currency': 11,
                'company': 12,  # FIXED: Column 12 contains Company, not PSP
                'kur': 22  # KUR kolonu
            }
        },
        'EKİM': {
            'header_row': 1,
            'cols': {
                'client': 2,
                'iban': 3,  # Kullanılmayacak
                'payment': 4,
                'psp': 5,  # FIXED: Column 5 contains PSP, not company
                'date': 6,
                'category': 7,
                'amount': 8,
                'commission': 9,
                'net': 10,
                'currency': 11,
                'company': 12,  # FIXED: Column 12 contains Company, not PSP
                'kur': 22  # KUR kolonu
            }
        },
        'KASIM': {
            'header_row': 1,
            'cols': {
                'client': 2,
                'iban': 3,  # Kullanılmayacak
                'payment': 4,
                'psp': 5,  # FIXED: Column 5 contains PSP, not company
                'date': 6,
                'category': 7,
                'amount': 8,
                'commission': 9,
                'net': 10,
                'currency': 11,
                'company': 12,  # FIXED: Column 12 contains Company, not PSP
                'kur': 22  # KUR kolonu
            }
        }
    }
    
    def __init__(self):
        self.errors = []
        self.warnings = []
        self.imported_count = 0
        self.skipped_count = 0
    
    def import_from_excel(self, file_path: str, sheet_names: List[str] = None) -> Dict[str, Any]:
        """
        Import transactions from Excel file
        
        Args:
            file_path: Path to Excel file
            sheet_names: List of sheet names to import (None = all sheets)
            
        Returns:
            Dict with import statistics
        """
        logger.info(f"Starting Excel import from: {file_path}")
        
        self.errors = []
        self.warnings = []
        self.imported_count = 0
        self.skipped_count = 0
        
        try:
            # Excel dosyasını oku
            xls = pd.ExcelFile(file_path)
            logger.info(f"Found {len(xls.sheet_names)} sheets in Excel file")
            
            # Eğer sheet_names belirtilmemişse, belirtilen sheet'leri al
            if sheet_names is None:
                sheet_names = ['HAZİRAN', 'TEMMUZ', 'AĞUSTOS', 'EYLÜL', 'EKİM', 'KASIM']
                # Sadece mevcut sheet'leri al
                sheet_names = [s for s in sheet_names if s in xls.sheet_names]
            
            logger.info(f"Will import from sheets: {sheet_names}")
            
            total_transactions = []
            
            # Her sayfa için import
            for sheet_name in sheet_names:
                logger.info(f"Processing sheet: {sheet_name}")
                
                try:
                    transactions = self._process_sheet(file_path, sheet_name)
                    total_transactions.extend(transactions)
                    logger.info(f"Processed {len(transactions)} transactions from {sheet_name}")
                except Exception as e:
                    # Hata durumunda tüm import'u durdur
                    error_msg = f"Error processing sheet {sheet_name}: {str(e)}"
                    logger.error(error_msg, exc_info=True)
                    self.errors.append(error_msg)
                    raise Exception(f"Import durduruldu: {error_msg}")
            
            # Database'e kaydet
            if total_transactions:
                logger.info(f"Saving {len(total_transactions)} transactions to database")
                self._save_to_database(total_transactions)
            
            return {
                'success': True,
                'imported_count': self.imported_count,
                'skipped_count': self.skipped_count,
                'total_count': len(total_transactions),
                'errors': self.errors,
                'warnings': self.warnings,
                'sheets_processed': len(sheet_names)
            }
            
        except Exception as e:
            error_msg = f"Failed to import Excel file: {str(e)}"
            logger.error(error_msg, exc_info=True)
            self.errors.append(error_msg)
            
            return {
                'success': False,
                'imported_count': self.imported_count,
                'skipped_count': self.skipped_count,
                'errors': self.errors,
                'warnings': self.warnings
            }
    
    def _process_sheet(self, file_path: str, sheet_name: str) -> List[Transaction]:
        """Process a single Excel sheet and return list of Transaction objects"""
        
        # Sheet config'i al
        if sheet_name not in self.SHEET_CONFIGS:
            raise ValueError(f"Unknown sheet structure: {sheet_name}")
        
        config = self.SHEET_CONFIGS[sheet_name]
        header_row = config['header_row']
        cols = config['cols']
        
        # Excel sayfasını raw olarak oku (header yok)
        df = pd.read_excel(file_path, sheet_name=sheet_name, header=None)
        
        logger.info(f"Sheet {sheet_name}: {len(df)} rows, {len(df.columns)} columns")
        
        # Find "Tür" column index from header row if it exists
        tur_col_idx = None
        if header_row < len(df):
            header_row_data = df.iloc[header_row]
            for col_idx in range(len(header_row_data)):
                cell_value = str(header_row_data[col_idx]).strip().upper()
                if 'TÜR' in cell_value or 'TUR' in cell_value:
                    tur_col_idx = col_idx
                    logger.info(f"Found 'Tür' column at index {col_idx} for sheet {sheet_name}")
                    break
        
        transactions = []
        
        # Her satır için (header_row'dan sonra)
        for idx in range(header_row + 1, len(df)):
            row = df.iloc[idx]
            
            # Check if "Tür" column exists and filter out "ÖDEME" rows
            if tur_col_idx is not None and tur_col_idx < len(row):
                if pd.notna(row[tur_col_idx]):
                    tur_value = str(row[tur_col_idx]).strip().upper()
                    if tur_value == 'ÖDEME':
                        self.skipped_count += 1
                        logger.debug(f"Sheet {sheet_name}, Satır {idx + 1}: Skipped 'ÖDEME' transaction")
                        continue
            
            try:
                transaction = self._parse_row(row, sheet_name, idx + 1, cols)
                if transaction:
                    transactions.append(transaction)
            except Exception as e:
                # Hata durumunda tüm import'u durdur
                error_msg = f"Sheet {sheet_name}, Satır {idx + 1}: {str(e)}"
                logger.error(error_msg, exc_info=True)
                raise Exception(error_msg)
        
        return transactions
    
    def _parse_row(self, row: pd.Series, sheet_name: str, row_num: int, cols: Dict[str, int]) -> Optional[Transaction]:
        """Parse a single row and create Transaction object"""
        
        # AD SOYAD
        client_col = cols['client']
        if pd.isna(row[client_col]) or not str(row[client_col]).strip():
            return None  # Boş satır, skip et
        
        client_name = str(row[client_col]).strip()
        
        # Toplam satırlarını atla
        if any(keyword in client_name.upper() for keyword in ['TOPLAM', 'TOTAL', 'SUM', 'GÜNLÜK', 'ÖZET', 'ZET']):
            return None
        
        # TARİH
        date_col = cols['date']
        if pd.isna(row[date_col]):
            raise ValueError(f"Tarih bos: Satır {row_num}")
        
        date_value = row[date_col]
        
        # Tarihi parse et
        if isinstance(date_value, pd.Timestamp):
            transaction_date = date_value.date()
        elif isinstance(date_value, datetime):
            transaction_date = date_value.date()
        else:
            try:
                transaction_date = pd.to_datetime(date_value).date()
            except:
                raise ValueError(f"Gecersiz tarih formati: {date_value}")
        
        # KATEGORİ
        category_col = cols['category']
        if pd.isna(row[category_col]):
            raise ValueError(f"Kategori bos: Satır {row_num}")
        
        category_raw = str(row[category_col]).strip().upper()
        category = self.CATEGORY_MAPPING.get(category_raw, category_raw)
        
        if category not in ['DEP', 'WD']:
            raise ValueError(f"Gecersiz kategori: {category_raw}")
        
        # TUTAR
        amount_col = cols['amount']
        if pd.isna(row[amount_col]):
            raise ValueError(f"Tutar bos: Satır {row_num}")
        
        try:
            amount = Decimal(str(row[amount_col]))
        except (InvalidOperation, ValueError) as e:
            raise ValueError(f"Gecersiz tutar: {row[amount_col]}")
        
        # WD (çekme) için tutarı her zaman negatif olarak işaretle
        if category == 'WD':
            amount = -abs(amount)
        
        # KOMİSYON
        commission_col = cols['commission']
        if pd.isna(row[commission_col]):
            commission = Decimal('0')
        else:
            try:
                commission = Decimal(str(row[commission_col]))
            except (InvalidOperation, ValueError):
                commission = Decimal('0')
        
        # NET
        net_col = cols['net']
        if pd.isna(row[net_col]):
            # Net hesapla
            if category == 'DEP':
                net_amount = amount - commission
            else:  # WD
                net_amount = amount + commission  # WD için amount negatif, commission pozitif
        else:
            try:
                net_amount = Decimal(str(row[net_col]))
            except (InvalidOperation, ValueError):
                # Hesapla
                if category == 'DEP':
                    net_amount = amount - commission
                else:
                    net_amount = amount + commission
        
        # WD için net_amount da her zaman negatif olmalı
        if category == 'WD':
            net_amount = -abs(net_amount)
        
        # PARA BİRİMİ
        currency_col = cols['currency']
        if pd.isna(row[currency_col]):
            currency = 'TL'  # Default
        else:
            currency_str = str(row[currency_col]).strip().upper()
            currency = self.CURRENCY_MAPPING.get(currency_str, currency_str)
        
        # Validate currency
        if currency not in ['TL', 'USD', 'EUR']:
            self.warnings.append(f"Satır {row_num}: Bilinmeyen para birimi '{currency_str}', TL olarak ayarlandi")
            currency = 'TL'
        
        # KASA (PSP)
        psp_col = cols['psp']
        if pd.isna(row[psp_col]):
            psp = None
        else:
            psp = str(row[psp_col]).strip()
            if not psp:
                psp = None
        
        # ŞİRKET
        company_col = cols['company']
        if pd.isna(row[company_col]):
            company = None
        else:
            company = str(row[company_col]).strip()
            if not company:
                company = None
        
        # ÖDEME ŞEKLİ
        payment_col = cols['payment']
        if pd.isna(row[payment_col]):
            payment_method = None
        else:
            payment_method = str(row[payment_col]).strip()
            if not payment_method:
                payment_method = None
        
        # KUR (exchange rate) - sadece USD için
        # Use daily KUR rates from DAILY_KUR_RATES mapping
        exchange_rate = None
        if currency == 'USD':
            # Format date as 'YYYY-MM-DD' for lookup
            date_key = transaction_date.strftime('%Y-%m-%d')
            if date_key in self.DAILY_KUR_RATES:
                exchange_rate = self.DAILY_KUR_RATES[date_key]
                logger.debug(f"Satır {row_num}: Using daily KUR rate {exchange_rate} for date {date_key}")
            else:
                # Fallback: try to find KUR in row if not in mapping
                kur_col = cols.get('kur')
                if kur_col is not None and kur_col < len(row):
                    if pd.notna(row[kur_col]):
                        try:
                            kur_value = row[kur_col]
                            # KUR değeri 20-50 arası olmalı
                            if isinstance(kur_value, (int, float)) and 20 < kur_value < 50:
                                exchange_rate = Decimal(str(kur_value))
                                logger.debug(f"Satır {row_num}: Using KUR from row: {exchange_rate}")
                            else:
                                self.warnings.append(f"Satır {row_num}: Gecersiz KUR değeri '{kur_value}' (20-50 arası olmalı)")
                        except (InvalidOperation, ValueError) as e:
                            self.warnings.append(f"Satır {row_num}: KUR parse hatası '{row[kur_col]}': {e}")
                
                # If still no exchange rate found, search in row
                if exchange_rate is None:
                    for col_idx in range(15, 25):
                        if col_idx < len(row) and pd.notna(row[col_idx]):
                            try:
                                kur_value = row[col_idx]
                                if isinstance(kur_value, (int, float)) and 20 < kur_value < 50:
                                    exchange_rate = Decimal(str(kur_value))
                                    logger.debug(f"Satır {row_num}: Found KUR in column {col_idx}: {exchange_rate}")
                                    break
                            except:
                                pass
                
                if exchange_rate is None:
                    self.warnings.append(f"Satır {row_num}: KUR rate not found for date {date_key} and not in row")
        
        # Transaction oluştur
        transaction = Transaction(
            client_name=client_name,
            date=transaction_date,
            category=category,
            amount=amount,  # WD için negatif, DEP için pozitif
            commission=abs(commission),  # Commission her zaman pozitif
            net_amount=net_amount,  # WD için negatif, DEP için pozitif
            currency=currency,
            psp=psp,
            company=company,
            payment_method=payment_method,
            exchange_rate=exchange_rate
        )
        
        # TRY tutarlarını hesapla
        transaction.calculate_try_amounts(exchange_rate)
        
        return transaction
    
    def _save_to_database(self, transactions: List[Transaction]):
        """Save transactions to database"""
        
        try:
            logger.info(f"Adding {len(transactions)} transactions to database session")
            
            # Batch insert için
            db.session.bulk_save_objects(transactions)
            db.session.commit()
            
            self.imported_count = len(transactions)
            logger.info(f"Successfully imported {self.imported_count} transactions")
            
        except Exception as e:
            db.session.rollback()
            error_msg = f"Database error: {str(e)}"
            logger.error(error_msg, exc_info=True)
            self.errors.append(error_msg)
            raise
    
    def update_psp_from_kasa(self, file_path: str, sheet_names: List[str] = None) -> Dict[str, Any]:
        """
        Update existing transactions' PSP field with KASA column values from Excel sheets.
        Matches transactions by client_name, date, and amount.
        
        Args:
            file_path: Path to Excel file
            sheet_names: List of sheet names to process (None = specified sheets)
            
        Returns:
            Dict with update statistics
        """
        logger.info(f"Starting PSP update from KASA column: {file_path}")
        
        self.errors = []
        self.warnings = []
        updated_count = 0
        not_found_count = 0
        
        try:
            # Excel dosyasını oku
            xls = pd.ExcelFile(file_path)
            logger.info(f"Found {len(xls.sheet_names)} sheets in Excel file")
            
            # Eğer sheet_names belirtilmemişse, belirtilen sheet'leri al
            if sheet_names is None:
                sheet_names = ['HAZİRAN', 'TEMMUZ', 'AĞUSTOS', 'EYLÜL', 'EKİM', 'KASIM']
                # Sadece mevcut sheet'leri al
                sheet_names = [s for s in sheet_names if s in xls.sheet_names]
            
            logger.info(f"Will update PSP from KASA for sheets: {sheet_names}")
            
            # Her sayfa için işle
            for sheet_name in sheet_names:
                logger.info(f"Processing sheet: {sheet_name}")
                
                try:
                    updated, not_found = self._update_psp_from_sheet(file_path, sheet_name)
                    updated_count += updated
                    not_found_count += not_found
                    logger.info(f"Updated {updated} transactions, {not_found} not found from {sheet_name}")
                except Exception as e:
                    error_msg = f"Error processing sheet {sheet_name}: {str(e)}"
                    logger.error(error_msg, exc_info=True)
                    self.errors.append(error_msg)
            
            # Commit all updates
            db.session.commit()
            
            return {
                'success': True,
                'updated_count': updated_count,
                'not_found_count': not_found_count,
                'errors': self.errors,
                'warnings': self.warnings,
                'sheets_processed': len(sheet_names)
            }
            
        except Exception as e:
            db.session.rollback()
            error_msg = f"Failed to update PSP from KASA: {str(e)}"
            logger.error(error_msg, exc_info=True)
            self.errors.append(error_msg)
            
            return {
                'success': False,
                'updated_count': updated_count,
                'not_found_count': not_found_count,
                'errors': self.errors,
                'warnings': self.warnings
            }
    
    def _update_psp_from_sheet(self, file_path: str, sheet_name: str) -> Tuple[int, int]:
        """
        Update PSP values from KASA column for a single sheet.
        Returns (updated_count, not_found_count)
        """
        if sheet_name not in self.SHEET_CONFIGS:
            raise ValueError(f"Unknown sheet structure: {sheet_name}")
        
        config = self.SHEET_CONFIGS[sheet_name]
        header_row = config['header_row']
        cols = config['cols']
        
        # Excel sayfasını raw olarak oku
        df = pd.read_excel(file_path, sheet_name=sheet_name, header=None)
        
        logger.info(f"Sheet {sheet_name}: {len(df)} rows, {len(df.columns)} columns")
        
        # Find KASA column from header row
        kasa_col_idx = None
        if header_row < len(df):
            header_row_data = df.iloc[header_row]
            for col_idx in range(len(header_row_data)):
                cell_value = str(header_row_data[col_idx]).strip().upper()
                if 'KASA' in cell_value:
                    kasa_col_idx = col_idx
                    logger.info(f"Found KASA column at index {col_idx} for sheet {sheet_name}")
                    break
        
        if kasa_col_idx is None:
            raise ValueError(f"KASA column not found in header row for sheet {sheet_name}")
        
        updated_count = 0
        not_found_count = 0
        
        # Her satır için (header_row'dan sonra)
        for idx in range(header_row + 1, len(df)):
            row = df.iloc[idx]
            
            try:
                # Extract transaction data for matching
                client_col = cols['client']
                if pd.isna(row[client_col]) or not str(row[client_col]).strip():
                    continue  # Skip empty rows
                
                client_name = str(row[client_col]).strip()
                
                # Skip total rows
                if any(keyword in client_name.upper() for keyword in ['TOPLAM', 'TOTAL', 'SUM', 'GÜNLÜK', 'ÖZET', 'ZET']):
                    continue
                
                # Extract date
                date_col = cols['date']
                if pd.isna(row[date_col]):
                    continue
                
                date_value = row[date_col]
                if isinstance(date_value, pd.Timestamp):
                    transaction_date = date_value.date()
                elif isinstance(date_value, datetime):
                    transaction_date = date_value.date()
                else:
                    try:
                        transaction_date = pd.to_datetime(date_value).date()
                    except:
                        continue
                
                # Extract amount
                amount_col = cols['amount']
                if pd.isna(row[amount_col]):
                    continue
                
                try:
                    amount = Decimal(str(row[amount_col]))
                except (InvalidOperation, ValueError):
                    continue
                
                # Extract KASA value (PSP)
                if pd.isna(row[kasa_col_idx]):
                    kasa_value = None
                else:
                    kasa_value = str(row[kasa_col_idx]).strip()
                    if not kasa_value:
                        kasa_value = None
                
                if kasa_value is None:
                    continue  # Skip if KASA is empty
                
                # Find matching transaction in database
                # Match by client_name, date, and amount (with tolerance for rounding)
                matching_transactions = Transaction.query.filter(
                    Transaction.client_name == client_name,
                    Transaction.date == transaction_date
                ).all()
                
                # Find best match by amount (considering absolute value for WD)
                matched_transaction = None
                min_diff = None
                
                for tx in matching_transactions:
                    # Compare absolute amounts (WD transactions have negative amounts)
                    tx_amount_abs = abs(tx.amount)
                    amount_abs = abs(amount)
                    
                    # Allow small difference for rounding (0.01 tolerance)
                    diff = abs(tx_amount_abs - amount_abs)
                    if diff <= Decimal('0.01'):
                        if min_diff is None or diff < min_diff:
                            min_diff = diff
                            matched_transaction = tx
                
                if matched_transaction:
                    # Update PSP with KASA value
                    if matched_transaction.psp != kasa_value:
                        logger.debug(f"Updating PSP for transaction {matched_transaction.id}: '{matched_transaction.psp}' -> '{kasa_value}'")
                        matched_transaction.psp = kasa_value
                        matched_transaction.updated_at = datetime.now(timezone.utc)
                        updated_count += 1
                else:
                    logger.warning(f"No matching transaction found: {client_name}, {transaction_date}, {amount}")
                    not_found_count += 1
                    
            except Exception as e:
                error_msg = f"Sheet {sheet_name}, Satır {idx + 1}: {str(e)}"
                logger.warning(error_msg)
                self.warnings.append(error_msg)
        
        return updated_count, not_found_count


# Global instance
excel_import_service = ExcelImportService()
