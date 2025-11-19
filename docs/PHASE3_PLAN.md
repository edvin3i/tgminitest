# Phase 3: TON Blockchain Integration - Implementation Plan

## 🎯 Overview

Integrate TON blockchain functionality to allow users to mint NFTs representing their quiz results.

## 📚 Technology Stack

### TON SDK Selection

**Primary SDK: pytoniq-tools**
- Purpose: NFT minting, wallet operations, direct blockchain interaction
- Advantages: Native Python, full control, no API limits
- Repository: https://github.com/nessshon/pytoniq-tools

**Secondary SDK: pytonapi**
- Purpose: Querying NFT data, account information, analytics
- Advantages: Simple REST API, well-documented, TonKeeper official
- Requires: API key from tonconsole.com
- Repository: https://github.com/tonkeeper/pytonapi

### Storage Solution

**IPFS via Pinata**
- Store NFT metadata JSON
- Store NFT images
- Free tier: 1GB storage, 100k requests/month
- Alternative: TON Storage (for future)

## 🗂️ Architecture

### Service Layer

```
app/services/ton/
├── __init__.py
├── wallet_service.py      # Wallet management, key generation
├── nft_service.py          # NFT minting, transfer operations
├── metadata_service.py     # NFT metadata generation
├── storage_service.py      # IPFS/Pinata integration
└── payment_service.py      # Telegram Stars, TON Connect
```

### API Layer

```
app/api/v1/endpoints/
├── nft.py                  # NFT endpoints
└── payments.py             # Payment endpoints
```

### Models (Already exist, may need updates)

```
app/models/
├── result.py              # MintTransaction, NFTMetadata
└── payment.py             # New: Payment model
```

## 📋 Implementation Checklist

### Step 1: Dependencies & Configuration ✅

- [x] Add pytoniq-tools to dependencies
- [x] Add pytonapi to dependencies
- [x] Add pinatapy-vourhey for IPFS
- [x] Add aiohttp for async requests
- [x] Update .env.example with TON variables
- [x] Create TON configuration in settings

### Step 2: Storage Service (IPFS)

- [ ] Create StorageService class
- [ ] Implement upload_image() method
- [ ] Implement upload_json() method
- [ ] Add retry logic for failed uploads
- [ ] Add cleanup for failed transactions
- [ ] Write tests with mocked Pinata API

### Step 3: Metadata Service

- [ ] Create MetadataService class
- [ ] Implement generate_nft_metadata()
  - [ ] Title: "{Result Type} - {Quiz Name}"
  - [ ] Description: User's result description
  - [ ] Image: Generated or template image
  - [ ] Attributes: quiz details, score, timestamp
- [ ] Create image templates for result types
- [ ] Add metadata validation
- [ ] Write tests for metadata generation

### Step 4: Wallet Service

- [ ] Create WalletService class
- [ ] Implement get_wallet() - load mnemonic from env
- [ ] Implement get_balance() - check wallet balance
- [ ] Add wallet health check
- [ ] Add low balance alerts
- [ ] Write tests with mocked wallet

### Step 5: NFT Service

- [ ] Create NFTService class
- [ ] Implement initialize_collection()
  - [ ] Deploy NFT collection contract (testnet)
  - [ ] Store collection address in config
- [ ] Implement mint_nft()
  - [ ] Generate metadata
  - [ ] Upload to IPFS
  - [ ] Create mint transaction
  - [ ] Wait for confirmation
  - [ ] Return NFT address
- [ ] Implement get_nft_details()
- [ ] Implement transfer_nft() (future)
- [ ] Add transaction retry logic
- [ ] Add error handling for all TON errors
- [ ] Write comprehensive tests

### Step 6: Payment Service

- [ ] Create PaymentService class
- [ ] Implement create_stars_invoice()
  - [ ] Amount: configurable (default 10 Stars)
  - [ ] Description: "Mint NFT for quiz result"
  - [ ] Payload: result_id
- [ ] Implement verify_stars_payment()
- [ ] Implement create_ton_payment() (TON Connect)
- [ ] Implement verify_ton_payment()
- [ ] Add webhook handler for payment confirmations
- [ ] Write payment tests

### Step 7: NFT API Endpoints

- [ ] POST /api/v1/nft/mint
  - [ ] Auth: require current user
  - [ ] Input: result_id
  - [ ] Check: result belongs to user
  - [ ] Check: not already minted
  - [ ] Create payment invoice
  - [ ] Return payment URL
- [ ] POST /api/v1/nft/mint/confirm
  - [ ] Auth: require current user
  - [ ] Input: payment_id, result_id
  - [ ] Verify payment
  - [ ] Trigger NFT minting (async)
  - [ ] Return mint_transaction_id
- [ ] GET /api/v1/nft/status/{transaction_id}
  - [ ] Return minting status
  - [ ] Return NFT address when complete
- [ ] GET /api/v1/users/me/nfts
  - [ ] List all user's minted NFTs
  - [ ] Include metadata
- [ ] GET /api/v1/nft/{address}/metadata
  - [ ] Fetch NFT metadata from IPFS
  - [ ] Return formatted data

### Step 8: Database Updates

- [ ] Add Payment model
  - [ ] Fields: user_id, amount, currency (STARS/TON), status, transaction_id
  - [ ] Relationships: user, result
- [ ] Update MintTransaction model
  - [ ] Add payment_id foreign key
  - [ ] Add retry_count field
  - [ ] Add error_message field
- [ ] Create Alembic migration
- [ ] Test migration up/down

### Step 9: Bot Integration

- [ ] Update result display handler
  - [ ] Add "Mint NFT" button
  - [ ] Show price (10 Stars or 0.1 TON)
- [ ] Create payment handler
  - [ ] Show payment options
  - [ ] Generate invoice
  - [ ] Send invoice to user
- [ ] Create payment callback handler
  - [ ] Verify payment
  - [ ] Trigger minting
  - [ ] Show minting status
- [ ] Create NFT gallery command
  - [ ] /mynfts - show user's NFTs
  - [ ] Display NFT cards with images
  - [ ] Add "View on Explorer" links
- [ ] Add error handling for all scenarios

### Step 10: Testing

- [ ] Unit tests for each service
- [ ] Integration tests for minting flow
- [ ] Test payment verification
- [ ] Test failed transaction handling
- [ ] Test concurrent minting requests
- [ ] Manual testnet testing
- [ ] Load testing for minting service

### Step 11: Monitoring & Logging

- [ ] Add structured logging for all TON operations
- [ ] Add metrics for minting success/failure rate
- [ ] Add alerts for low wallet balance
- [ ] Add alerts for failed transactions
- [ ] Create admin dashboard endpoint for TON stats

## 🔧 Configuration

### Environment Variables (New)

```env
# TON Network
TON_NETWORK=testnet  # testnet or mainnet
TON_API_KEY=your_tonapi_key_from_tonconsole

# Wallet (Mnemonic stored securely)
TON_WALLET_MNEMONIC="word1 word2 ... word24"
TON_WALLET_VERSION=v4r2

# NFT Collection
NFT_COLLECTION_ADDRESS=EQD...  # Deployed collection address

# IPFS/Pinata
PINATA_API_KEY=your_pinata_api_key
PINATA_SECRET_KEY=your_pinata_secret_key

# Payment
NFT_MINT_PRICE_STARS=10
NFT_MINT_PRICE_TON=0.1
PAYMENT_PROVIDER_TOKEN=your_telegram_payment_provider_token
```

## 📊 Success Metrics

### Technical Metrics
- [ ] NFT minting success rate > 95%
- [ ] Average minting time < 30 seconds
- [ ] Payment verification accuracy 100%
- [ ] Zero unauthorized mints
- [ ] Wallet balance never drops to 0

### Business Metrics
- [ ] 10+ successful NFT mints on testnet
- [ ] All test cases passing
- [ ] No critical bugs in production
- [ ] Documentation complete

## 🚀 Deployment Plan

### Testnet Phase (Week 1-2)
1. Deploy NFT collection to testnet
2. Test with test wallets
3. Verify all flows work correctly
4. Fix any bugs found

### Mainnet Preparation (Week 3)
1. Security audit of all code
2. Load testing
3. Create monitoring dashboards
4. Prepare runbook for issues

### Mainnet Deployment (Week 4)
1. Deploy collection to mainnet
2. Update environment variables
3. Enable for limited users (beta)
4. Monitor closely
5. Gradually roll out to all users

## 🔐 Security Considerations

1. **Wallet Security**
   - Mnemonic stored in encrypted environment variable
   - Never log mnemonic
   - Use separate hot wallet for minting (not main treasury)
   - Implement spending limits

2. **Payment Verification**
   - Always verify payment before minting
   - Check payment amount matches price
   - Verify payment is from correct user
   - Handle double-spending attempts

3. **Rate Limiting**
   - Limit minting requests per user (max 5 per day)
   - Prevent spam attacks
   - Add cooldown between mints

4. **Error Handling**
   - Never expose internal errors to users
   - Log all errors securely
   - Implement proper retry logic
   - Add circuit breakers for TON API

## 📝 Notes

- Start with testnet, move to mainnet only after thorough testing
- Keep wallet balance monitored at all times
- Implement proper error handling before payment integration
- Document all TON-specific errors and their solutions
- Create admin tools for manual intervention if needed

## ⏱️ Timeline

- **Week 1**: Storage, Metadata, Wallet services
- **Week 2**: NFT service, Payment service
- **Week 3**: API endpoints, Bot integration
- **Week 4**: Testing, Documentation, Deployment

**Total**: 4 weeks for complete Phase 3
