from Crypto.Hash import keccak
import binascii
import whirlpool

text = 'blockchain'
data = text.encode("utf8")

keccak512 = keccak.new(data = data, digest_bits = 512).digest()
print("Keccak512: ", binascii.hexlify(keccak512))

whirlpool512 = whirlpool.new(data).digest()
print("Whirlpool512: ", binascii.hexlify(whirlpool512))