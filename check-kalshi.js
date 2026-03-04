const https = require('https');
const fs = require('fs');
const crypto = require('crypto');

const KEY_ID = '6a059c14-f547-4f49-ad75-0e2784679b5d';
const PRIVATE_KEY = fs.readFileSync('/Users/carterwalsh/.openclaw/workspace/kalshi-key.pem', 'utf8');
const ORDER_IDS = [
  'a2fb4cab-4d39-4cef-a0cb-e17196a5320f',
  'ea21c1ba-9fec-4b24-b608-f975fbb017bc',
  '3ade790e-ab2a-4229-a7ec-416969ce69e2',
  '26380991-7d5f-4227-9d31-4e0d2bd293ce'
];

function signRequest(method, path, body) {
  const timestamp = Math.floor(Date.now() / 1000).toString();
  const bodyHash = crypto.createHash('sha256').update(body || '').digest('hex');
  const signedContent = timestamp + method + path + bodyHash;
  
  const sign = crypto.createSign('RSA-SHA256');
  sign.update(signedContent);
  // Use PSS padding
  const signature = sign.sign({ key: PRIVATE_KEY, padding: crypto.constants.RSA_PKCS1_PSS_PADDING, saltLength: crypto.constants.RSA_PSS_SALTLEN_DIGEST });
  return {
    signature: signature.toString('base64'),
    timestamp,
    keyId: KEY_ID
  };
}

async function getOrder(orderId) {
  return new Promise((resolve, reject) => {
    const path = '/trade-api/v2/orders/' + orderId;
    const method = 'GET';
    const { signature, timestamp, keyId } = signRequest(method, path, '');
    
    const options = {
      hostname: 'api.elections.kalshi.com',
      path: path,
      method: method,
      headers: {
        'KALSHI-KEY-ID': keyId,
        'KALSHI-SIGNATURE': signature,
        'KALSHI-TIMESTAMP': timestamp,
        'Content-Type': 'application/json'
      }
    };
    
    const req = https.request(options, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => {
        try {
          resolve(JSON.parse(data));
        } catch(e) {
          resolve({error: data});
        }
      });
    });
    
    req.on('error', reject);
    req.end();
  });
}

async function getBalance() {
  return new Promise((resolve, reject) => {
    const path = '/trade-api/v2/balance';
    const method = 'GET';
    const { signature, timestamp, keyId } = signRequest(method, path, '');
    
    const options = {
      hostname: 'api.elections.kalshi.com',
      path: path,
      method: method,
      headers: {
        'KALSHI-KEY-ID': keyId,
        'KALSHI-SIGNATURE': signature,
        'KALSHI-TIMESTAMP': timestamp,
        'Content-Type': 'application/json'
      }
    };
    
    const req = https.request(options, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => {
        try {
          resolve(JSON.parse(data));
        } catch(e) {
          resolve({error: data});
        }
      });
    });
    
    req.on('error', reject);
    req.end();
  });
}

async function main() {
  console.log('=== ORDER STATUS ===');
  for (const id of ORDER_IDS) {
    try {
      const result = await getOrder(id);
      const order = result.order || result;
      console.log('\n' + id.slice(0,8) + '...');
      console.log('  Status: ' + (order.status || 'UNKNOWN'));
      console.log('  Market: ' + (order.market_id || 'N/A'));
      console.log('  Side: ' + (order.side || 'N/A') + ' | Qty: ' + (order.size || 0));
      console.log('  Price: ' + (order.price || 'N/A') + ' | Filled: ' + (order.filled_size || 0));
    } catch(e) {
      console.log('\n' + id.slice(0,8) + '... ERROR: ' + e.message);
    }
  }
  
  console.log('\n=== BALANCE ===');
  try {
    const bal = await getBalance();
    console.log('  Cash: $' + (bal.currency_balance || bal.available_balance || 'N/A'));
    console.log('  Available: $' + (bal.available_balance || 'N/A'));
  } catch(e) {
    console.log('  ERROR: ' + e.message);
  }
}

main();
