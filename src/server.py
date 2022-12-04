import subprocess,os
import random
import json,yaml
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization



from fastapi import FastAPI
import uvicorn

from models.vm import VM

max_limit_vm = 10
vm_data_dir = '/'.join(os.getcwd().split('\\')[:-1])

ymal_data = {
    'users':['default',{'name':'name','sudo':'ALL=(ALL) NOPASSWD:ALL','ssh_authorized_keys':['key']}],
}

def read_json_and_update(cpu,ram):
    
    new_config = None
    with open('../vmconfig.json','r') as config_file:
        config = json.load(config_file)
        new_config = config
    
    with open('../config.json','w') as new_config_file:
        new_config['machine-config']['vcpu_count'] = cpu
        new_config['machine-config']['mem_size_mib'] = ram
        
        json.dump(new_config,new_config_file)


def create_required_files():
    
    vm_name = 'vm-' + ''.join(random.choice('0123456789') for i in range(4))  + '' + ''.join(random.choice('abcdefghijklmnopqrstuvwxyz') for i in range(8))
    while(os.path.exists(vm_data_dir+'/'+vm_name)):
        print(f"dir exist {vm_name}")
        vm_name = 'vm-' + ''.join(random.choice('0123456789') for i in range(4))  + '' + ''.join(random.choice('abcdefghijklmnopqrstuvwxyz') for i in range(8))
    
    os.mkdir(vm_data_dir+'/'+vm_name)
    new_vm_dir_path = vm_data_dir+'/'+vm_name + '/'
    # ssh_command = ['ssh-keygen', '-C', vm_name,'-f', new_vm_dir_path  + 'ssh-key']
    # ssh = subprocess.run(ssh_command,text=True) 
    
    # output = ssh.stdout.readlines() 
    # print(output)
    
    # ssh.stdin.write(b'\n')   
    
    # output = ssh.stdout.readline() 
    # print(output)
    # ssh.stdin.write(b'\n')   
    
    # output = ssh.stdout.readline() 
    # print(output)
    
    private_key = rsa.generate_private_key(
    public_exponent=65537,
    key_size=2048
    )
    
    private_key_pass = b"\n"

    encrypted_pem_private_key = private_key.private_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PrivateFormat.PKCS8,
    encryption_algorithm=serialization.BestAvailableEncryption(private_key_pass)
    )

    # print(encrypted_pem_private_key.splitlines()[0])
    # b'-----BEGIN ENCRYPTED PRIVATE KEY-----'

    pem_public_key = private_key.public_key().public_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PublicFormat.SubjectPublicKeyInfo
    )

    pem_public_key = pem_public_key.decode()
    pem_public_key = pem_public_key.splitlines()
    pem_public_key.pop(0)
    pem_public_key.pop()
    pem_public_key = ''.join(pem_public_key)
    
    pem_public_key = 'ssh-rsa '+ pem_public_key + ' ' + vm_name


    
    unencrypted_pem_private_key = private_key.private_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PrivateFormat.TraditionalOpenSSL,
    encryption_algorithm=serialization.NoEncryption()
)

    private_key_file = open(new_vm_dir_path+ vm_name, "w")
    private_key_file.write(encrypted_pem_private_key.decode())
    private_key_file.close()

    public_key_file = open(new_vm_dir_path+ vm_name+ ".pub", "w")
    public_key_file.write(pem_public_key)
    public_key_file.close()
    
    
    vm_yaml = ymal_data
    vm_yaml['users'][1]['name'] = vm_name
    vm_yaml['users'][1]['ssh_authorized_keys'] = pem_public_key
    
    yaml_path = new_vm_dir_path + 'config.yaml'
    with open(yaml_path,'w') as config:
        yaml.dump(vm_yaml, config)
        
    return vm_name,yaml_path,new_vm_dir_path


def apply_command(vm_name,vm_ram,vm_disk,vm_cpu,ymal_file,vm_path):
    
    vm_create =subprocess.run( ['multipass','launch','-n','lts','--name',vm_name,'--mem',vm_ram,'--disk',vm_disk,'--cpus',vm_cpu,'--cloud-init',ymal_file],stdout=subprocess.PIPE, text=True,)
    vm_info = subprocess.run(['multipass', 'info', vm_name],stdout=subprocess.PIPE, text=True,)
    
    with open(vm_path +  vm_name + '.txt','w') as config_data:
        config_data.write(vm_info)

    return vm_info

app = FastAPI()

@app.post('/create_vm')
async def start_vm(vm:VM):
    
   
    vm_name,yaml_path,vm_path =  create_required_files()
    vm_info  = apply_command(vm_name=vm_name,vm_ram= vm.ram,vm_disk= vm.disk,vm_cpu =vm.cpu,ymal_file=yaml_path,vm_path=vm_path)
    ans = subprocess.run(['ls'],stdout=subprocess.PIPE, text=True,)
    
    return ans.stdout,vm_info


if __name__=="__main__":
    uvicorn.run("server:app",host='0.0.0.0', port=8080, reload=True)