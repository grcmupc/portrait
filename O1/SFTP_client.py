import pysftp, os
import xml.etree.ElementTree as ET

full_path = os.path.realpath(__file__)
path, filename = os.path.split(full_path)
os.chdir(path)

#SFTP SERVER DATA


def SFTP_PM_reporting(Hostname, Port, Username, Password, folder):
    cnopts = pysftp.CnOpts()
    cnopts.hostkeys = None   

    #Establish SFTP connection with SFTP server
    with pysftp.Connection(host=Hostname, username=Username, password=Password, port=Port, cnopts=cnopts) as sftp:
        print("Connection successfully established ... ")
        # Switch to a remote directory
        sftp.cwd(folder)

        #Obtain directory structure
        directory_structure = sftp.listdir_attr()

        remoteFilePath = directory_structure[-1].filename #Read last file
        # Use get method to download a file
        sftp.get(remoteFilePath)

    
def process_PM_measurements(file_name):
    # Passing the path of the xml document to enable the parsing process
    tree = ET.parse(file_name)

    # getting the parent tag of the xml document
    root = tree.getroot()

    #Register namespace
    ET.register_namespace('md',"{http://www.3gpp.org/ftp/specs/archive/28_series/28.550#measData}")

    #Namespace from xml
    ns={'md' : "http://www.3gpp.org/ftp/specs/archive/28_series/28.550#measData"}

    #Print type and value: 
    print(root.find(".//md:measType[@p='1']",ns).text,":",root.find(".//md:r[@p='1']",ns).text)
    print(root.find(".//md:measType[@p='2']",ns).text,":",root.find(".//md:r[@p='2']",ns).text)
    print(root.find(".//md:measType[@p='3']",ns).text,":",root.find(".//md:r[@p='3']",ns).text)
    print(root.find(".//md:measType[@p='4']",ns).text,":",root.find(".//md:r[@p='4']",ns).text)
    print(root.find(".//md:measType[@p='5']",ns).text,":",root.find(".//md:r[@p='5']",ns).text)

if __name__ == '__main__':
    Hostname = '192.168.0.2'
    Username = 'usr'
    Password = 'pass'
    Port=2222
    file_name='xml_PM_report_sample.xml'
    folder='/SFTP_server_folder/'

    SFTP_PM_reporting(Hostname, Port, Username, Password, folder)

    process_PM_measurements(file_name)