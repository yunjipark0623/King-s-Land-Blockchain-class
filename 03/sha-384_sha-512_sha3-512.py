import hashlib, binascii

text = 'blockchain'
data = text.encode("utf8")
print(data)

sha384hash = hashlib.sha384(data).digest()
print("SHA-384: ", binascii.hexlify(sha384hash))

sha512hash = hashlib.sha512(data).digest()
print("SHA-512: ", binascii.hexlify(sha512hash))

sha3_512hash = hashlib.sha3_512(data).digest()
print("SHA3-512: ", binascii.hexlify(sha3_512hash))