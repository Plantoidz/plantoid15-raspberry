import hashlib
remote_output_file = "https://replicate.delivery/pbxt/IXwp8o1MXaa9Mx7WJK1jKjp5gGvOLWpr4hEmRUq4IdphdXiE/out.mp4"
md5sum = hashlib.md5(remote_output_file.encode('utf-8')).hexdigest()
print(md5sum)
