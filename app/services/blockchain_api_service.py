"""
Blockchain API service for fetching Trust wallet transactions
Supports Ethereum, BSC, and TRON networks
"""
import requests
import time
import logging
import os
from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
import json

logger = logging.getLogger(__name__)

@dataclass
class BlockchainTransaction:
    """Data class for blockchain transaction"""
    transaction_hash: str
    block_number: int
    block_timestamp: datetime
    from_address: str
    to_address: str
    token_symbol: str
    token_name: Optional[str]
    token_address: Optional[str]
    token_amount: Decimal
    token_decimals: int
    transaction_type: str  # IN, OUT, INTERNAL
    gas_fee: Decimal
    gas_fee_token: str
    status: str
    confirmations: int
    network: str

class BlockchainAPIService:
    """Service for fetching blockchain transactions from various networks"""
    
    def __init__(self):
        # API endpoints for different networks
        self.api_endpoints = {
            'ETH': 'https://api.etherscan.io/v2/api',
            'BSC': 'https://api.bscscan.com/api',
            'TRC': 'https://api.trongrid.io'
        }
        
        # API keys from environment variables
        self.api_keys = {
            'ETH': os.getenv('ETHERSCAN_API_KEY', 'GXBSPXEZJKKNI7BTQZ9JWK35IQSNCDW2DK'),
            'BSC': os.getenv('BSCSCAN_API_KEY', 'GXBSPXEZJKKNI7BTQZ9JWK35IQSNCDW2DK'),  # BSC now uses Etherscan API
            'TRC': os.getenv('TRONGRID_API_KEY', '43e9fc59-8830-4946-8967-957cb72726d3')
        }
        
        # Token contract addresses for major tokens
        self.token_contracts = {
            'ETH': {
                'USDT': '0xdAC17F958D2ee523a2206206994597C13D831ec7',
                'USDC': '0xA0b86a33E6441b8C4C8C0E1234567890abcdef12',
                'DAI': '0x6B175474E89094C44Da98b954EedeAC495271d0F',
                'WETH': '0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2',
            },
            'BSC': {
                'USDT': '0x55d398326f99059fF775485246999027B3197955',
                'USDC': '0x8AC76a51cc950d9822D68b83fE1Ad97B32Cd580d',
                'BNB': '0xbb4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c',
                'BUSD': '0xe9e7CEA3DedcA5984780Bafc599bD69ADd087D56',
            },
            'TRC': {
                'USDT': 'TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t',
                'USDC': 'TEkxiTehnzSmSe2XqrBj4w32RUN966rdz8',
                'TRX': 'T9yD14Nj9j7xAB4dbGeiX9h8unkKHxuWwb',
            }
        }
        
        # Token symbols mapping
        self.token_symbols = {
            'ETH': {'ETH': 'ETH', '0x': 'ETH'},  # Native ETH
            'BSC': {'BNB': 'BNB', '0x': 'BNB'},  # Native BNB
            'TRC': {'TRX': 'TRX', 'T': 'TRX'},   # Native TRX
        }
        
        # Rate limiting
        self.rate_limits = {
            'ETH': {'requests_per_second': 5, 'last_request': 0},
            'BSC': {'requests_per_second': 5, 'last_request': 0},
            'TRC': {'requests_per_second': 10, 'last_request': 0},
        }
    
    def _rate_limit(self, network: str):
        """Apply rate limiting for API calls"""
        current_time = time.time()
        rate_limit = self.rate_limits[network]
        
        time_since_last = current_time - rate_limit['last_request']
        min_interval = 1.0 / rate_limit['requests_per_second']
        
        if time_since_last < min_interval:
            sleep_time = min_interval - time_since_last
            time.sleep(sleep_time)
        
        self.rate_limits[network]['last_request'] = time.time()
    
    def _make_request(self, url: str, params: Dict, network: str) -> Dict:
        """Make HTTP request with error handling"""
        self._rate_limit(network)
        
        try:
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            # Handle different response formats
            result = response.json()
            
            # TronGrid API returns data in 'data' field
            if isinstance(result, dict) and 'data' in result:
                return result
            
            # Etherscan/BSCScan return 'result' field
            return result
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed for {network}: {e}")
            # Return empty result instead of raising
            return {'data': []}
        except Exception as e:
            logger.error(f"Error parsing API response for {network}: {e}")
            return {'data': []}
    
    def get_ethereum_transactions(self, wallet_address: str, start_block: int = 0, end_block: int = None) -> List[BlockchainTransaction]:
        """Fetch Ethereum transactions"""
        transactions = []
        
        # Get normal transactions
        normal_txs = self._get_ethereum_normal_transactions(wallet_address, start_block, end_block)
        transactions.extend(normal_txs)
        
        # Get ERC-20 token transactions
        token_txs = self._get_ethereum_token_transactions(wallet_address, start_block, end_block)
        transactions.extend(token_txs)
        
        return transactions
    
    def _get_ethereum_normal_transactions(self, wallet_address: str, start_block: int, end_block: int) -> List[BlockchainTransaction]:
        """Get normal ETH transactions with FULL PAGINATION"""
        logger.info(f"Fetching ALL ETH transactions for {wallet_address} (with pagination)")
        
        transactions = []
        page = 1
        max_pages = 50  # Safety limit
        
        while page <= max_pages:
            params = {
                'chainid': '1',  # Ethereum mainnet
                'module': 'account',
                'action': 'txlist',
                'address': wallet_address,
                'startblock': start_block,
                'endblock': end_block or 'latest',
                'page': page,
                'offset': 10000,  # Max records per page
                'sort': 'asc',
                'apikey': self.api_keys['ETH']
            }
            
            logger.info(f"Fetching ETH transactions page {page}")
            response = self._make_request(self.api_endpoints['ETH'], params, 'ETH')
            
            # Check if response is valid
            if 'status' not in response:
                logger.error(f"Invalid Etherscan response: {response}")
                break
            
            if response['status'] != '1':
                error_msg = response.get('message', 'Unknown error')
                if page == 1:
                    logger.warning(f"No Ethereum transactions found for {wallet_address}: {error_msg}")
                break
            
            # Handle empty result
            if 'result' not in response or not response['result']:
                logger.info(f"No more ETH transactions on page {page}")
                break
            
            # Check if result is actually an error message
            if isinstance(response['result'], str):
                logger.warning(f"Etherscan returned error: {response['result']}")
                break
            
            result = response['result']
            
            if page == 1:
                logger.info(f"First page: {len(result)} ETH transactions")
            
            # Process transactions from this page
            for tx in result:
                try:
                    # Determine transaction type
                    tx_type = 'IN' if tx['to'].lower() == wallet_address.lower() else 'OUT'
                    
                    transaction = BlockchainTransaction(
                        transaction_hash=tx['hash'],
                        block_number=int(tx['blockNumber']),
                        block_timestamp=datetime.fromtimestamp(int(tx['timeStamp']), tz=timezone.utc),
                        from_address=tx['from'],
                        to_address=tx['to'],
                        token_symbol='ETH',
                        token_name='Ethereum',
                        token_address=None,
                        token_amount=Decimal(tx['value']) / Decimal(10**18),  # Convert from Wei
                        token_decimals=18,
                        transaction_type=tx_type,
                        gas_fee=Decimal(tx['gasUsed']) * Decimal(tx['gasPrice']) / Decimal(10**18),
                        gas_fee_token='ETH',
                        status='CONFIRMED' if tx['isError'] == '0' else 'FAILED',
                        confirmations=int(tx['confirmations']),
                        network='ETH'
                    )
                    transactions.append(transaction)
                except Exception as e:
                    logger.error(f"Error parsing Ethereum transaction {tx.get('hash', 'unknown')}: {e}")
                    continue
            
            # If less than offset, we got all transactions
            if len(result) < 10000:
                logger.info(f"Reached last page for ETH at page {page} ({len(result)} transactions)")
                break
            
            logger.info(f"ETH page {page} complete: {len(transactions)} total ETH transactions so far")
            page += 1
        
        logger.info(f"Fetched {len(transactions)} TOTAL Ethereum transactions")
        return transactions
    
    def _get_ethereum_token_transactions(self, wallet_address: str, start_block: int, end_block: int) -> List[BlockchainTransaction]:
        """Get ERC-20 token transactions with FULL PAGINATION"""
        transactions = []
        
        # Token name mapping
        token_names = {
            'USDT': 'Tether USD',
            'USDC': 'USD Coin',
            'DAI': 'Dai Stablecoin',
            'WETH': 'Wrapped Ethereum',
            'ETH': 'Ethereum'
        }
        
        # Get ALL transactions for each known token with pagination
        for token_symbol, contract_address in self.token_contracts['ETH'].items():
            logger.info(f"Fetching ALL {token_symbol} transactions for {wallet_address} (with pagination)")
            
            page = 1
            max_pages = 50  # Safety limit: 50 pages * 10,000 = 500,000 transactions max per token
            
            while page <= max_pages:
                params = {
                    'chainid': '1',  # Ethereum mainnet
                    'module': 'account',
                    'action': 'tokentx',
                    'contractaddress': contract_address,
                    'address': wallet_address,
                    'startblock': start_block,
                    'endblock': end_block or 'latest',
                    'page': page,
                    'offset': 10000,  # Max records per page (Etherscan limit)
                    'sort': 'asc',
                    'apikey': self.api_keys['ETH']
                }
                
                logger.info(f"Fetching {token_symbol} page {page}")
                response = self._make_request(self.api_endpoints['ETH'], params, 'ETH')
                
                # Check response status
                if response.get('status') != '1':
                    if page == 1:
                        logger.info(f"No {token_symbol} transactions found: {response.get('message', 'Unknown error')}")
                    break
                
                # Get transactions from response
                result = response.get('result', [])
                
                # If result is a string (error message), break
                if isinstance(result, str):
                    logger.warning(f"Etherscan returned error for {token_symbol}: {result}")
                    break
                
                # If no transactions, we're done
                if not result:
                    logger.info(f"No more {token_symbol} transactions on page {page}")
                    break
                
                if page == 1:
                    logger.info(f"First page: {len(result)} {token_symbol} transactions")
                
                # Process transactions from this page
                for tx in result:
                    try:
                        # Determine transaction type
                        tx_type = 'IN' if tx['to'].lower() == wallet_address.lower() else 'OUT'
                        
                        transaction = BlockchainTransaction(
                            transaction_hash=tx['hash'],
                            block_number=int(tx['blockNumber']),
                            block_timestamp=datetime.fromtimestamp(int(tx['timeStamp']), tz=timezone.utc),
                            from_address=tx['from'],
                            to_address=tx['to'],
                            token_symbol=token_symbol,
                            token_name=token_names.get(token_symbol, ''),
                            token_address=contract_address,
                            token_amount=Decimal(tx['value']) / Decimal(10**int(tx['tokenDecimal'])),
                            token_decimals=int(tx['tokenDecimal']),
                            transaction_type=tx_type,
                            gas_fee=Decimal(tx['gasUsed']) * Decimal(tx['gasPrice']) / Decimal(10**18),
                            gas_fee_token='ETH',
                            status='CONFIRMED',
                            confirmations=int(tx['confirmations']),
                            network='ETH'
                        )
                        transactions.append(transaction)
                    except Exception as e:
                        logger.error(f"Error parsing token transaction {tx.get('hash', 'unknown')}: {e}")
                        continue
                
                # If less than offset, we got all transactions
                if len(result) < 10000:
                    logger.info(f"Reached last page for {token_symbol} at page {page} ({len(result)} transactions)")
                    break
                
                logger.info(f"{token_symbol} page {page} complete: {len([t for t in transactions if t.token_symbol == token_symbol])} total {token_symbol} transactions so far")
                page += 1
        
        logger.info(f"Fetched {len(transactions)} TOTAL Ethereum token transactions")
        return transactions
    
    def get_bsc_transactions(self, wallet_address: str, start_block: int = 0, end_block: int = None) -> List[BlockchainTransaction]:
        """Fetch BSC transactions (similar to Ethereum)"""
        transactions = []
        
        # Get normal BNB transactions
        normal_txs = self._get_bsc_normal_transactions(wallet_address, start_block, end_block)
        transactions.extend(normal_txs)
        
        # Get BEP-20 token transactions
        token_txs = self._get_bsc_token_transactions(wallet_address, start_block, end_block)
        transactions.extend(token_txs)
        
        return transactions
    
    def _get_bsc_normal_transactions(self, wallet_address: str, start_block: int, end_block: int) -> List[BlockchainTransaction]:
        """Get normal BNB transactions with FULL PAGINATION"""
        logger.info(f"Fetching ALL BNB transactions for {wallet_address} (with pagination)")
        
        transactions = []
        page = 1
        max_pages = 50  # Safety limit
        
        while page <= max_pages:
            params = {
                'module': 'account',
                'action': 'txlist',
                'address': wallet_address,
                'startblock': start_block,
                'endblock': end_block or 'latest',
                'page': page,
                'offset': 10000,  # Max records per page
                'sort': 'asc',
                'apikey': self.api_keys['BSC']
            }
            
            logger.info(f"Fetching BNB transactions page {page}")
            response = self._make_request(self.api_endpoints['BSC'], params, 'BSC')
            
            if response.get('status') != '1':
                if page == 1:
                    logger.warning(f"No BSC transactions found: {response.get('message', 'Unknown error')}")
                break
            
            # Get transactions from response
            result = response.get('result', [])
            
            # If result is a string (error message), break
            if isinstance(result, str):
                logger.warning(f"BscScan returned error: {result}")
                break
            
            # If no transactions, we're done
            if not result:
                logger.info(f"No more BNB transactions on page {page}")
                break
            
            if page == 1:
                logger.info(f"First page: {len(result)} BNB transactions")
            
            # Process transactions from this page
            for tx in result:
                try:
                    tx_type = 'IN' if tx['to'].lower() == wallet_address.lower() else 'OUT'
                    
                    transaction = BlockchainTransaction(
                        transaction_hash=tx['hash'],
                        block_number=int(tx['blockNumber']),
                        block_timestamp=datetime.fromtimestamp(int(tx['timeStamp']), tz=timezone.utc),
                        from_address=tx['from'],
                        to_address=tx['to'],
                        token_symbol='BNB',
                        token_name='Binance Coin',
                        token_address=None,
                        token_amount=Decimal(tx['value']) / Decimal(10**18),
                        token_decimals=18,
                        transaction_type=tx_type,
                        gas_fee=Decimal(tx['gasUsed']) * Decimal(tx['gasPrice']) / Decimal(10**18),
                        gas_fee_token='BNB',
                        status='CONFIRMED' if tx['isError'] == '0' else 'FAILED',
                        confirmations=int(tx['confirmations']),
                        network='BSC'
                    )
                    transactions.append(transaction)
                except Exception as e:
                    logger.error(f"Error parsing BSC transaction {tx.get('hash', 'unknown')}: {e}")
                    continue
            
            # If less than offset, we got all transactions
            if len(result) < 10000:
                logger.info(f"Reached last page for BNB at page {page} ({len(result)} transactions)")
                break
            
            logger.info(f"BNB page {page} complete: {len(transactions)} total BNB transactions so far")
            page += 1
        
        logger.info(f"Fetched {len(transactions)} TOTAL BNB transactions")
        return transactions
    
    def _get_bsc_token_transactions(self, wallet_address: str, start_block: int, end_block: int) -> List[BlockchainTransaction]:
        """Get BEP-20 token transactions with FULL PAGINATION"""
        transactions = []
        
        # Token name mapping
        token_names = {
            'USDT': 'Tether USD',
            'USDC': 'USD Coin',
            'BUSD': 'Binance USD',
            'BNB': 'Binance Coin'
        }
        
        # Get ALL transactions for each known token with pagination
        for token_symbol, contract_address in self.token_contracts['BSC'].items():
            logger.info(f"Fetching ALL {token_symbol} transactions for {wallet_address} (with pagination)")
            
            page = 1
            max_pages = 50  # Safety limit: 50 pages * 10,000 = 500,000 transactions max per token
            
            while page <= max_pages:
                params = {
                    'module': 'account',
                    'action': 'tokentx',
                    'contractaddress': contract_address,
                    'address': wallet_address,
                    'startblock': start_block,
                    'endblock': end_block or 'latest',
                    'page': page,
                    'offset': 10000,  # Max records per page (BscScan limit)
                    'sort': 'asc',
                    'apikey': self.api_keys['BSC']
                }
                
                logger.info(f"Fetching {token_symbol} page {page}")
                response = self._make_request(self.api_endpoints['BSC'], params, 'BSC')
                
                # Check response status
                if response.get('status') != '1':
                    if page == 1:
                        logger.info(f"No {token_symbol} transactions found: {response.get('message', 'Unknown error')}")
                    break
                
                # Get transactions from response
                result = response.get('result', [])
                
                # If result is a string (error message), break
                if isinstance(result, str):
                    logger.warning(f"BscScan returned error for {token_symbol}: {result}")
                    break
                
                # If no transactions, we're done
                if not result:
                    logger.info(f"No more {token_symbol} transactions on page {page}")
                    break
                
                if page == 1:
                    logger.info(f"First page: {len(result)} {token_symbol} transactions")
                
                # Process transactions from this page
                for tx in result:
                    try:
                        tx_type = 'IN' if tx['to'].lower() == wallet_address.lower() else 'OUT'
                        
                        transaction = BlockchainTransaction(
                            transaction_hash=tx['hash'],
                            block_number=int(tx['blockNumber']),
                            block_timestamp=datetime.fromtimestamp(int(tx['timeStamp']), tz=timezone.utc),
                            from_address=tx['from'],
                            to_address=tx['to'],
                            token_symbol=token_symbol,
                            token_name=token_names.get(token_symbol, ''),
                            token_address=contract_address,
                            token_amount=Decimal(tx['value']) / Decimal(10**int(tx['tokenDecimal'])),
                            token_decimals=int(tx['tokenDecimal']),
                            transaction_type=tx_type,
                            gas_fee=Decimal(tx['gasUsed']) * Decimal(tx['gasPrice']) / Decimal(10**18),
                            gas_fee_token='BNB',
                            status='CONFIRMED',
                            confirmations=int(tx['confirmations']),
                            network='BSC'
                        )
                        transactions.append(transaction)
                    except Exception as e:
                        logger.error(f"Error parsing BSC token transaction {tx.get('hash', 'unknown')}: {e}")
                        continue
                
                # If less than offset, we got all transactions
                if len(result) < 10000:
                    logger.info(f"Reached last page for {token_symbol} at page {page} ({len(result)} transactions)")
                    break
                
                logger.info(f"{token_symbol} page {page} complete: {len([t for t in transactions if t.token_symbol == token_symbol])} total {token_symbol} transactions so far")
                page += 1
        
        logger.info(f"Fetched {len(transactions)} TOTAL BSC token transactions")
        return transactions
    
    def get_tron_transactions(self, wallet_address: str, start_block: int = 0, end_block: int = None) -> List[BlockchainTransaction]:
        """Fetch TRON transfers using TronGrid API - focusing on token transfers only"""
        transactions = []
        
        # Skip TRX transfers (users want to see token transfers, not native TRX transactions)
        # Most wallets don't need TRX transaction history, they need transfer history
        
        # Get TRC-20 and TRC721 token transfers
        token_txs = self._get_tron_token_transactions(wallet_address, start_block, end_block)
        transactions.extend(token_txs)
        
        # Get TRC1155 transfers (optional - for NFT transfers)
        trc1155_txs = self._get_tron_trc1155_transactions(wallet_address, start_block, end_block)
        transactions.extend(trc1155_txs)
        
        return transactions
    
    def _get_tron_normal_transactions(self, wallet_address: str, start_block: int, end_block: int) -> List[BlockchainTransaction]:
        """Get TRX and TRC10 transfers from TronGrid API"""
        logger.info(f"Fetching TRON TRX & TRC10 transfers for {wallet_address}")
        
        transactions = []
        
        try:
            # Use TronGrid API (public, no authentication required)
            # Get account transactions
            url = f"https://api.trongrid.io/v1/accounts/{wallet_address}/transactions"
            params = {
                'only_confirmed': 'true',
                'limit': 200
            }
            headers = {
                'TRON-PRO-API-KEY': self.api_keys['TRC']
            }
            
            response = requests.get(url, params=params, headers=headers, timeout=30)
            logger.info(f"TronGrid transactions API - Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                
                if isinstance(data, dict) and 'data' in data:
                    tx_list = data.get('data', [])
                    
                    # Log first transaction fields to understand API response structure
                    if len(tx_list) > 0 and logger.level <= logging.DEBUG:
                        logger.debug(f"Sample TRX transfer fields: {list(tx_list[0].keys())}")
                    
                    logger.info(f"Processing {len(tx_list)} TRX & TRC10 transfers")
                    
                    for tx in tx_list:
                        try:
                            # Parse TRX/TRC10 transfer
                            to_addr = tx.get('to_address', tx.get('toAddress', '')).strip()
                            from_addr = tx.get('from_address', tx.get('fromAddress', tx.get('ownerAddress', ''))).strip()
                            
                            # Skip if addresses are invalid
                            if not from_addr or not to_addr:
                                continue
                            
                            tx_type = 'IN' if to_addr.lower() == wallet_address.lower() else 'OUT'
                            
                            # Get amount
                            amount_str = tx.get('amount', tx.get('value', '0'))
                            token_type = tx.get('type', 'TRX')
                            
                            # Handle different amount formats
                            try:
                                if isinstance(amount_str, str):
                                    # Remove commas if present
                                    amount_str = amount_str.replace(',', '')
                                
                                # For TRX and TRC10, amount is in sun (1 TRX = 1,000,000 sun)
                                if token_type in ['TRX', 'TRC10']:
                                    amount_int = int(float(str(amount_str)))
                                    trx_amount = Decimal(amount_int) / Decimal(1000000)
                                    
                                    # Skip if amount is essentially zero
                                    if trx_amount < Decimal('0.000001'):
                                        continue
                                else:
                                    # For other types, try to parse directly
                                    trx_amount = Decimal(str(amount_str))
                            except (ValueError, TypeError) as e:
                                logger.warning(f"Could not parse amount: {amount_str} for tx {tx.get('hash', '')[:10]}")
                                continue
                            
                            # Get timestamp
                            timestamp = tx.get('block_timestamp', tx.get('timestamp', 0))
                            if timestamp > 0:
                                tx_timestamp = datetime.fromtimestamp(timestamp / 1000, tz=timezone.utc)
                            else:
                                tx_timestamp = datetime.now(timezone.utc)
                            
                            # Determine token symbol
                            if token_type == 'TRC10':
                                token_symbol = tx.get('token_symbol', 'TRC10')
                                token_address = tx.get('token_address', '')
                            else:
                                token_symbol = 'TRX'
                                token_address = None
                            
                            transaction = BlockchainTransaction(
                                transaction_hash=tx.get('hash', tx.get('transaction', '')),
                                block_number=int(tx.get('block', tx.get('block_number', 0))),
                                block_timestamp=tx_timestamp,
                                from_address=from_addr,
                                to_address=to_addr,
                                token_symbol=token_symbol,
                                token_address=token_address,
                                token_amount=trx_amount,
                                token_decimals=6,
                                transaction_type=tx_type,
                                gas_fee=Decimal(0),
                                gas_fee_token='TRX',
                                status='CONFIRMED',
                                confirmations=int(tx.get('confirmed', 1)),
                                network='TRC'
                            )
                            transactions.append(transaction)
                        except Exception as e:
                            logger.error(f"Error parsing TRON transfer: {e}")
                            continue
                else:
                    logger.warning(f"Unexpected API response format")
                            
        except Exception as e:
            logger.error(f"Error fetching TRON transfers: {e}")
        
        logger.info(f"Fetched {len(transactions)} TRON transfers")
        return transactions
    
    def _get_tron_token_transactions(self, wallet_address: str, start_block: int, end_block: int) -> List[BlockchainTransaction]:
        """Get TRC-20 and TRC721 token transfers from Tronscan API with FULL PAGINATION"""
        logger.info(f"Fetching ALL TRON token transfers for {wallet_address} (with pagination)")
        
        transactions = []
        
        try:
            # Use TronGrid API with pagination to get ALL transactions
            url = f"https://api.trongrid.io/v1/accounts/{wallet_address}/transactions/trc20"
            headers = {
                'TRON-PRO-API-KEY': self.api_keys['TRC']
            }
            
            # Pagination loop - fetch ALL transactions
            fingerprint = None
            page_num = 0
            max_pages = 100  # Safety limit: 100 pages * 200 = 20,000 transactions max
            
            while page_num < max_pages:
                page_num += 1
                
                params = {
                    'only_confirmed': 'true',
                    'limit': 200  # Max per page
                }
                
                # Add fingerprint for pagination (next page)
                if fingerprint:
                    params['fingerprint'] = fingerprint
                
                logger.info(f"Fetching TRC20 page {page_num}, fingerprint: {fingerprint}")
                
                response = requests.get(url, params=params, headers=headers, timeout=30)
                
                if response.status_code != 200:
                    error_text = response.text[:500] if response.text else "No error message"
                    logger.error(f"TRON API returned non-200 status: {response.status_code}, Response: {error_text}")
                    # Don't break immediately - log and try to continue if it's a rate limit
                    if response.status_code == 429:
                        logger.warning("Rate limited by TronGrid API, waiting 2 seconds...")
                        time.sleep(2)
                        continue
                    break
                
                try:
                    data = response.json()
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse JSON response from TronGrid API: {e}, Response text: {response.text[:200]}")
                    break
                
                if not isinstance(data, dict):
                    logger.error(f"Unexpected response format: {type(data)}")
                    break
                
                # Check for API errors in response
                if 'success' in data and not data.get('success'):
                    error_msg = data.get('error', data.get('message', 'Unknown API error'))
                    logger.error(f"TronGrid API returned error: {error_msg}")
                    break
                
                # Get transactions from this page
                tx_list = data.get('data', [])
                
                if page_num == 1:
                    logger.info(f"First page: {len(tx_list)} TRON token transfers")
                    if tx_list:
                        logger.info(f"Sample TRC20 transfer keys: {list(tx_list[0].keys())}")
                
                # If no transactions, we're done
                if not tx_list:
                    logger.info(f"No more transactions on page {page_num}. Pagination complete.")
                    break
                
                # Process transactions from this page
                for idx, tx in enumerate(tx_list):
                    try:
                        # TronGrid API format - check actual field names
                        from_addr = tx.get('from', '').strip()
                        to_addr = tx.get('to', '').strip()
                        
                        # Skip if address is invalid
                        if not from_addr or not to_addr:
                            continue
                        
                        # Determine transaction type
                        tx_type = 'IN' if to_addr.lower() == wallet_address.lower() else 'OUT'
                        
                        # Get token info - TronGrid uses 'token_info'
                        token_info = tx.get('token_info', {})
                        
                        # Extract token symbol with fallback logic
                        token_symbol = token_info.get('symbol') or tx.get('token_symbol') or 'UNKNOWN'
                        token_name = token_info.get('name', '')
                        token_address = token_info.get('address', tx.get('token_address', ''))
                        
                        # Get amount - TronGrid format
                        amount_str = tx.get('value', '0')
                        decimals = int(token_info.get('decimals', 6))  # decimals are in token_info
                        
                        # Handle amount - might be in different formats
                        try:
                            if isinstance(amount_str, str):
                                # Remove commas if present
                                amount_str = amount_str.replace(',', '')
                            amount = Decimal(str(amount_str)) / Decimal(10 ** decimals)
                        except (ValueError, TypeError) as e:
                            logger.warning(f"Could not parse amount: {amount_str} for token {token_symbol}")
                            continue
                        
                        # Parse timestamp (in milliseconds)
                        timestamp = tx.get('block_timestamp', tx.get('timestamp', 0))
                        if timestamp > 0:
                            tx_timestamp = datetime.fromtimestamp(timestamp / 1000, tz=timezone.utc)
                        else:
                            tx_timestamp = datetime.now(timezone.utc)
                        
                        # Get transaction hash - TronGrid uses 'transaction_id'
                        tx_hash = tx.get('transaction_id', '')
                        
                        # Get block number if available
                        block_num = tx.get('block', tx.get('block_number', 0))
                        if isinstance(block_num, str):
                            try:
                                block_num = int(block_num)
                            except:
                                block_num = 0
                        else:
                            block_num = int(block_num)
                        
                        transaction = BlockchainTransaction(
                            transaction_hash=tx_hash,
                            block_number=block_num,
                            block_timestamp=tx_timestamp,
                            from_address=from_addr,
                            to_address=to_addr,
                            token_symbol=token_symbol,
                            token_name=token_name,
                            token_address=token_address,
                            token_amount=amount,
                            token_decimals=decimals,
                            transaction_type=tx_type,
                            gas_fee=Decimal(0),
                            gas_fee_token='TRX',
                            status='CONFIRMED',
                            confirmations=int(tx.get('confirmed', 0)),
                            network='TRC'
                        )
                        transactions.append(transaction)
                    except Exception as e:
                        logger.error(f"Error parsing TRON token transfer: {e}", exc_info=True)
                        continue
                
                # Get fingerprint for next page
                meta = data.get('meta', {})
                fingerprint = meta.get('fingerprint')
                
                logger.info(f"Page {page_num}: Got {len(tx_list)} transactions, fingerprint: {fingerprint}, meta keys: {list(meta.keys()) if meta else 'None'}")
                
                # If no fingerprint or less than limit, we're on the last page
                if not fingerprint or len(tx_list) < 200:
                    logger.info(f"Reached last page at page {page_num} ({len(tx_list)} transactions)")
                    break
                
                logger.info(f"Page {page_num} complete: {len(transactions)} total transactions so far, continuing to next page...")
                
        except Exception as e:
            logger.error(f"Error fetching TRON token transfers: {e}", exc_info=True)
        
        logger.info(f"Fetched {len(transactions)} TOTAL TRON token transfers across {page_num} pages")
        return transactions
    
    def _get_tron_trc1155_transactions(self, wallet_address: str, start_block: int, end_block: int) -> List[BlockchainTransaction]:
        """Get TRC1155 token transfers from Tronscan API"""
        logger.info(f"Fetching TRON TRC1155 transfers for {wallet_address}")
        
        transactions = []
        
        try:
            # Use Tronscan API for TRC1155 token transfers
            # https://apilist.tronscanapi.com/api/token_trc1155/transfers
            url = "https://apilist.tronscanapi.com/api/token_trc1155/transfers"
            params = {
                'address': wallet_address,
                'limit': 200,
                'start': 0,
                'filterTokenValue': '0'  # No filter for NFTs
            }
            
            # Add timestamp filters if provided
            if start_block and start_block > 0:
                params['start_timestamp'] = start_block * 1000
            if end_block and end_block > 0:
                params['end_timestamp'] = end_block * 1000
            
            response = requests.get(url, params=params, timeout=30)
            
            if response.status_code != 200:
                logger.debug(f"TRC1155 API returned non-200 status: {response.status_code}")
                return transactions
            
            data = response.json()
            
            if isinstance(data, dict):
                tx_list = data.get('data', [])
                
                if len(tx_list) > 0:
                    logger.info(f"Processing {len(tx_list)} TRON TRC1155 transfers")
                
                for tx in tx_list:
                    try:
                        from_addr = tx.get('from_address', '').strip()
                        to_addr = tx.get('to_address', '').strip()
                        
                        if not from_addr or not to_addr:
                            continue
                        
                        tx_type = 'IN' if to_addr.lower() == wallet_address.lower() else 'OUT'
                        
                        token_symbol = tx.get('token_symbol', 'TRC1155')
                        token_address = tx.get('contract_address', '')
                        token_id = tx.get('token_id', '')
                        
                        # For NFTs, amount is typically 1
                        amount_str = tx.get('amount', '1')
                        try:
                            if isinstance(amount_str, str):
                                amount_str = amount_str.replace(',', '')
                            amount = Decimal(str(amount_str))
                        except (ValueError, TypeError):
                            amount = Decimal(1)
                        
                        timestamp = tx.get('block_timestamp', tx.get('timestamp', 0))
                        if timestamp > 0:
                            tx_timestamp = datetime.fromtimestamp(timestamp / 1000, tz=timezone.utc)
                        else:
                            tx_timestamp = datetime.now(timezone.utc)
                        
                        # Create NFT-specific token symbol
                        if token_id:
                            token_symbol = f"{token_symbol} #{token_id}"
                        
                        transaction = BlockchainTransaction(
                            transaction_hash=tx.get('transaction', tx.get('hash', '')),
                            block_number=int(tx.get('block', tx.get('block_number', 0))),
                            block_timestamp=tx_timestamp,
                            from_address=from_addr,
                            to_address=to_addr,
                            token_symbol=token_symbol,
                            token_address=token_address,
                            token_amount=amount,
                            token_decimals=0,  # NFTs don't have decimals
                            transaction_type=tx_type,
                            gas_fee=Decimal(0),
                            gas_fee_token='TRX',
                            status='CONFIRMED',
                            confirmations=int(tx.get('confirmed', 0)),
                            network='TRC'
                        )
                        transactions.append(transaction)
                    except Exception as e:
                        logger.error(f"Error parsing TRON TRC1155 transfer: {e}", exc_info=True)
                        continue
                        
        except Exception as e:
            logger.debug(f"Error fetching TRON TRC1155 transfers: {e}")
        
        if transactions:
            logger.info(f"Fetched {len(transactions)} TRON TRC1155 transfers")
        return transactions
    
    def get_wallet_transactions(self, wallet_address: str, network: str, start_block: int = 0, end_block: int = None) -> List[BlockchainTransaction]:
        """Get transactions for a specific wallet and network"""
        try:
            if network == 'ETH':
                return self.get_ethereum_transactions(wallet_address, start_block, end_block)
            elif network == 'BSC':
                return self.get_bsc_transactions(wallet_address, start_block, end_block)
            elif network == 'TRC':
                return self.get_tron_transactions(wallet_address, start_block, end_block)
            else:
                logger.error(f"Unsupported network: {network}")
                return []
        except Exception as e:
            logger.error(f"Error fetching transactions for {wallet_address} on {network}: {e}")
            return []
    
    def get_wallet_balance(self, wallet_address: str, network: str) -> Dict[str, float]:
        """Get wallet balance for native token and major tokens"""
        try:
            balances = {}
            
            if network == 'ETH':
                # Get ETH balance
                eth_balance = self._get_ethereum_balance(wallet_address)
                balances['ETH'] = eth_balance
                
                # Get major token balances
                for token_symbol, contract_address in self.token_contracts['ETH'].items():
                    if token_symbol != 'ETH':  # Skip ETH as it's already handled
                        token_balance = self._get_ethereum_token_balance(wallet_address, contract_address, token_symbol)
                        if token_balance > 0:
                            balances[token_symbol] = token_balance
            
            elif network == 'BSC':
                # Get BNB balance
                bnb_balance = self._get_bsc_balance(wallet_address)
                balances['BNB'] = bnb_balance
                
                # Get major token balances
                for token_symbol, contract_address in self.token_contracts['BSC'].items():
                    if token_symbol != 'BNB':  # Skip BNB as it's already handled
                        token_balance = self._get_bsc_token_balance(wallet_address, contract_address, token_symbol)
                        if token_balance > 0:
                            balances[token_symbol] = token_balance
            
            elif network == 'TRC':
                # Get TRX balance
                trx_balance = self._get_tron_balance(wallet_address)
                balances['TRX'] = trx_balance
                
                # Get all token balances in one call
                token_balances = self._get_tron_all_token_balances(wallet_address)
                balances.update(token_balances)
            
            return balances
            
        except Exception as e:
            logger.error(f"Error getting wallet balance for {wallet_address} on {network}: {e}")
            return {}
    
    def _get_ethereum_balance(self, wallet_address: str) -> float:
        """Get ETH balance"""
        logger.info(f"Fetching ETH balance for {wallet_address} with API key: {self.api_keys['ETH'][:10]}..." if self.api_keys['ETH'] else "No API key set")
        
        params = {
            'chainid': '1',  # Ethereum mainnet
            'module': 'account',
            'action': 'balance',
            'address': wallet_address,
            'tag': 'latest',
            'apikey': self.api_keys['ETH']
        }
        
        logger.info(f"Etherscan balance API URL: {self.api_endpoints['ETH']}")
        logger.info(f"Etherscan balance API params: {params}")
        
        response = self._make_request(self.api_endpoints['ETH'], params, 'ETH')
        logger.info(f"Etherscan balance API response: {response}")
        
        if response.get('status') == '1':
            wei_balance = int(response['result'])
            eth_balance = wei_balance / (10**18)  # Convert from Wei to ETH
            logger.info(f"ETH balance for {wallet_address}: {eth_balance} ETH ({wei_balance} wei)")
            return eth_balance
        else:
            logger.warning(f"Failed to get ETH balance: {response.get('message', 'Unknown error')}")
            return 0.0
    
    def _get_ethereum_token_balance(self, wallet_address: str, contract_address: str, token_symbol: str) -> float:
        """Get ERC-20 token balance"""
        params = {
            'chainid': '1',  # Ethereum mainnet
            'module': 'account',
            'action': 'tokenbalance',
            'contractaddress': contract_address,
            'address': wallet_address,
            'tag': 'latest',
            'apikey': self.api_keys['ETH']
        }
        
        response = self._make_request(self.api_endpoints['ETH'], params, 'ETH')
        if response['status'] == '1':
            token_balance = int(response['result'])
            # Get token decimals
            decimals = 18  # Default for most tokens
            if token_symbol in ['USDT', 'USDC']:
                decimals = 6
            return token_balance / (10**decimals)
        return 0.0
    
    def _get_bsc_balance(self, wallet_address: str) -> float:
        """Get BNB balance"""
        params = {
            'module': 'account',
            'action': 'balance',
            'address': wallet_address,
            'tag': 'latest',
            'apikey': self.api_keys['BSC']
        }
        
        response = self._make_request(self.api_endpoints['BSC'], params, 'BSC')
        if response['status'] == '1':
            wei_balance = int(response['result'])
            return wei_balance / (10**18)  # Convert from Wei to BNB
        return 0.0
    
    def _get_bsc_token_balance(self, wallet_address: str, contract_address: str, token_symbol: str) -> float:
        """Get BEP-20 token balance"""
        params = {
            'module': 'account',
            'action': 'tokenbalance',
            'contractaddress': contract_address,
            'address': wallet_address,
            'tag': 'latest',
            'apikey': self.api_keys['BSC']
        }
        
        response = self._make_request(self.api_endpoints['BSC'], params, 'BSC')
        if response['status'] == '1':
            token_balance = int(response['result'])
            # Get token decimals
            decimals = 18  # Default for most tokens
            if token_symbol in ['USDT', 'USDC']:
                decimals = 6
            return token_balance / (10**decimals)
        return 0.0
    
    def _get_tron_balance(self, wallet_address: str) -> float:
        """Get TRX balance using TronGrid API"""
        try:
            url = f"https://api.trongrid.io/wallet/getaccount"
            payload = {
                "address": wallet_address,
                "visible": True
            }
            headers = {
                'TRON-PRO-API-KEY': self.api_keys['TRC']
            }
            
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            if response.status_code == 200:
                data = response.json()
                balance_sun = int(data.get('balance', 0))
                balance_trx = balance_sun / 1_000_000  # Convert from sun to TRX
                return balance_trx
            return 0.0
        except Exception as e:
            logger.error(f"Error fetching TRX balance: {e}")
            return 0.0
    
    def _get_tron_all_token_balances(self, wallet_address: str) -> Dict[str, float]:
        """Get all TRC-20 token balances using TronGrid API"""
        balances = {}
        
        try:
            # Use the account endpoint to get token balances
            url = f"https://api.trongrid.io/v1/accounts/{wallet_address}"
            headers = {
                'TRON-PRO-API-KEY': self.api_keys['TRC']
            }
            
            response = requests.get(url, headers=headers, timeout=30)
            logger.info(f"TronGrid Account API - Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                account_data = data.get('data', [])
                
                if not account_data:
                    logger.warning("No account data returned")
                    return balances
                
                trc20_tokens = account_data[0].get('trc20', [])
                logger.info(f"TRC20 data type: {type(trc20_tokens)}")
                logger.info(f"TRC20 raw data: {trc20_tokens}")
                logger.info(f"Found {len(trc20_tokens) if isinstance(trc20_tokens, (list, dict)) else 0} TRC20 tokens in account")
                
                # Log first token structure for debugging
                if trc20_tokens and isinstance(trc20_tokens, list):
                    logger.info(f"Sample TRC20 token structure: {trc20_tokens[0]}")
                elif trc20_tokens and isinstance(trc20_tokens, dict):
                    logger.info(f"Sample TRC20 token structure: {dict(list(trc20_tokens.items())[:1])}")
                
                # Handle dictionary format {contract_address: balance}
                if isinstance(trc20_tokens, dict):
                    for token_address, balance_str in trc20_tokens.items():
                        try:
                            logger.info(f"Processing token at {token_address}, balance: {balance_str}")
                            
                            # Skip if no balance
                            if not balance_str or balance_str == '0':
                                continue
                            
                            # Known token addresses mapping for faster lookup
                            known_tokens = {
                                'TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t': {'symbol': 'USDT', 'decimals': 6},
                                'TXLAQ63Xg1NAzckPwKHvzw7CSEmLMEqcdj': {'symbol': 'USDC', 'decimals': 6},
                            }
                            
                            token_address_lower = token_address.lower()
                            if token_address_lower in {k.lower(): v for k, v in known_tokens.items()}:
                                token_info = known_tokens[token_address]
                                symbol = token_info['symbol']
                                decimals = token_info['decimals']
                                logger.info(f"Using cached info for {symbol}")
                            else:
                                # Try to fetch from contract API
                                token_info_url = f"https://api.trongrid.io/v1/contracts/{token_address}"
                                token_info_resp = requests.get(token_info_url, headers=headers, timeout=5)
                                
                                if token_info_resp.status_code == 200:
                                    token_info_data = token_info_resp.json()
                                    logger.info(f"Token info response: {token_info_data}")
                                    token_info = token_info_data.get('data', [{}])[0] if isinstance(token_info_data.get('data'), list) else token_info_data.get('data', {})
                                    symbol = token_info.get('symbol', 'UNKNOWN')
                                    decimals = int(token_info.get('decimals', 18))
                                else:
                                    # Fallback
                                    symbol = f"UNKNOWN_{token_address[:8]}"
                                    decimals = 18
                                    logger.warning(f"Could not fetch token info for {token_address}")
                            
                            # Convert balance from raw value to decimal
                            balance_raw = int(balance_str)
                            balance_decimal = balance_raw / (10 ** decimals)
                            
                            if balance_decimal > 0:
                                balances[symbol] = balance_decimal
                                logger.info(f"Added token {symbol}: {balance_decimal}")
                            else:
                                logger.info(f"Skipping zero balance token {symbol}")
                                
                        except Exception as e:
                            logger.error(f"Error processing token balance: {e}", exc_info=True)
                            continue
                
                # Handle list format [{contract_address: balance}]
                elif isinstance(trc20_tokens, list):
                    for token_dict in trc20_tokens:
                        if isinstance(token_dict, dict):
                            for token_address, balance_str in token_dict.items():
                                try:
                                    logger.info(f"Processing list token at {token_address}, balance: {balance_str}")
                                    
                                    # Skip if no balance
                                    if not balance_str or balance_str == '0':
                                        continue
                                    
                                    # Known token addresses mapping for faster lookup
                                    known_tokens = {
                                        'TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t': {'symbol': 'USDT', 'decimals': 6},
                                        'TXLAQ63Xg1NAzckPwKHvzw7CSEmLMEqcdj': {'symbol': 'USDC', 'decimals': 6},
                                    }
                                    
                                    token_address_lower = token_address.lower()
                                    if token_address_lower in {k.lower(): v for k, v in known_tokens.items()}:
                                        token_info = known_tokens[token_address]
                                        symbol = token_info['symbol']
                                        decimals = token_info['decimals']
                                        logger.info(f"Using cached info for {symbol}")
                                    else:
                                        # Try to fetch from contract API
                                        token_info_url = f"https://api.trongrid.io/v1/contracts/{token_address}"
                                        token_info_resp = requests.get(token_info_url, headers=headers, timeout=5)
                                        
                                        if token_info_resp.status_code == 200:
                                            token_info_data = token_info_resp.json()
                                            logger.info(f"Token info response: {token_info_data}")
                                            token_info = token_info_data.get('data', [{}])[0] if isinstance(token_info_data.get('data'), list) else token_info_data.get('data', {})
                                            symbol = token_info.get('symbol', 'UNKNOWN')
                                            decimals = int(token_info.get('decimals', 18))
                                        else:
                                            # Fallback
                                            symbol = f"UNKNOWN_{token_address[:8]}"
                                            decimals = 18
                                            logger.warning(f"Could not fetch token info for {token_address}")
                                    
                                    # Convert balance from raw value to decimal
                                    balance_raw = int(balance_str)
                                    balance_decimal = balance_raw / (10 ** decimals)
                                    
                                    if balance_decimal > 0:
                                        balances[symbol] = balance_decimal
                                        logger.info(f"Added token {symbol}: {balance_decimal}")
                                    else:
                                        logger.info(f"Skipping zero balance token {symbol}")
                                        
                                except Exception as e:
                                    logger.error(f"Error processing list token balance: {e}", exc_info=True)
                                    continue
            else:
                logger.error(f"Failed to fetch account data: {response.status_code}")
                
        except Exception as e:
            logger.error(f"Error fetching all token balances: {e}", exc_info=True)
        
        return balances
    
    def _get_tron_token_balance(self, wallet_address: str, contract_address: str, token_symbol: str) -> float:
        """Get a specific TRC-20 token balance (for backward compatibility)"""
        try:
            all_balances = self._get_tron_all_token_balances(wallet_address)
            return all_balances.get(token_symbol, 0.0)
        except Exception as e:
            logger.error(f"Error fetching token balance for {token_symbol}: {e}")
            return 0.0
