import binascii, scrypt

passwd = "p@$$w0rd~3"
print(passwd)
salt = "7b07a2977a473e84fc30d463a2333bcfea6cb3400b16bec4e17fe981c925ba4f"
print("Salt: ", salt)

key = scrypt.hash(passwd, salt, 16384, 16, 1, 32)
print("Derived key:", binascii.hexlify(key))

