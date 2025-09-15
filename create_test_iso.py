import pycdlib
from io import BytesIO

def main():
    print("Creating a clean test ISO using pycdlib...")

    iso = pycdlib.PyCdlib()
    iso.new(joliet=True, rock_ridge='1.09') # Corrected Rock Ridge version

    # Add a file to the root
    iso.add_fp(BytesIO(b"This is file1.txt\n"), 18, '/FILE1.TXT', rr_name='file1.txt')

    # Add a directory
    iso.add_directory('/SUBDIR', rr_name='subdir')

    # Add a file to the subdirectory
    iso.add_fp(BytesIO(b"This is file2.txt in a subdir\n"), 31, '/SUBDIR/FILE2.TXT', rr_name='file2.txt')

    # Write the ISO
    iso.write('test.iso')
    iso.close()

    print("Successfully created test.iso")

if __name__ == "__main__":
    main()
