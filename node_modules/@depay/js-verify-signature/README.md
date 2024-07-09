## Installation

### Node.js

```
yarn add @depay/js-verify-signature
```

or 

```
npm install --save @depay/js-verify-signature
```

### Web

Web does not need to install crypto nor atob dependencies, but it needs to use the `js-verify-signature-web` package:

```
yarn add @depay/js-verify-signature-web
```

or 

```
npm install --save @depay/js-verify-signature-web
```

## Functionality

```javascript
import { verify } from '@depay/js-verify-signature'

const data = "Sign me!"
const signature = "AVovd+VSNI/6bg4E4eH+VI/neFuLxREKRqjtOFAMafSOTR9m0B96bBJdAxJ8\n8raPMCkg6R80uc48kV5UsaKCTbo4W+KUHlXONS2RPJz2DCO6E8Kq9K3h7GbB\nO2PUWAD/r4zALkp8gFymyte5E/iRq8AEHTjaPtuYltIzfP7TV8sW3nhFxrTG\nBWG4/fIgb1m+KsAYD19dOSpghOvhJC/WbMJOIt4YeiyZDU9I9G+F5dl6so/m\nxm93jkUq2mJnV8vuXjqRn/KrcTFZPxNTQVSTF/oOpVjXMsPLyJqJxS7giq2u\n2Y/4qquDzmiCdqK8woqrBP13cf0+kkeYS9lmJ14fTQ==\n"
const publicKey = "-----BEGIN PUBLIC KEY-----\nMIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA7Uao+6ZgMCCJmvTeOZY7\nf33PZrclAygUoVObqMka3GEGZTcHeBMxGAzs2upwjtn7OcMej7EoVGPDnPaNlgdW\nWRYXe/HG5M4yqSJWbPpuEejxVuNd8DWCKn1V0lvlVy/SCdzBaU0RCvuSiW0PoEla\nsAQr5jKr+R8ORnnU7EZlfAeol07T0AHeB1HBRNuRkBZY+KjN3eOmGMP1ClPJfLhK\nDS7pB1/lfZoPEIYdvB0r6EujKrZv88kLZXFb/OVnr/OsVEpriZlKWWWFTNaMnAHp\n330g1dVh0oEHoiz98G/sFHhr4TsQlp+avfpOlaaVNVf+WuFEIohJspj1MSHdmv6L\n3QIDAQAB\n-----END PUBLIC KEY-----\n"

let verified = await verify({ signature, publicKey, data })
// true
```

## Development

### Get started

```
yarn install
yarn test
```
