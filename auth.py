import bcrypt
import os
# Implement the password hashing function
def hash_password (plain_text_password):
 # Encode the password to bytes, required by bcrypt
  password_bytes = plain_text_password.encode("UTF-8")
 # Generate a salt and hash the password
  salt = bcrypt.gensalt()
  hashed_password =bcrypt.hashpw(password_bytes, salt)
 # Decode the hash back to a string to share in a text file
  return hashed_password

# Implement the password verification function
def verify_password(plain_text_password, hashed_password):
  # Encode both the plaintext password and stored hash to bytes
   password_bytes = plain_text_password.encode("utf-8")
   hashed_password_bytes = hashed_password_bytes.encode("utf-8")
  # bcrypt.checkpw handles extracting the salt and comparing
   return bcrypt.checkpw(password_bytes, hashed_password_bytes)

# Test you hashing functions
 # TEMPORARY TEST CODE - Remove after testing
   test_password = "TopSecurePassword1234"
 # Test Hashing
   hashed = hash_password(test_password)  
   print(f"Original password: {}")




