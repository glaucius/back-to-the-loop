#!/usr/bin/env python3

"""
Script para testar a conectividade e configuração do MinIO
Útil para debugging de problemas de bucket público
"""

import sys
import json
import requests
from minio import Minio
from minio.error import S3Error

def test_minio_connection():
    """Testa conexão e configuração do MinIO"""
    
    # Configurações
    endpoint = "localhost:9000"
    access_key = "minioadmin"
    secret_key = "minioadmin123"
    bucket_name = "btl-images"
    
    print("🔍 Testando configuração do MinIO...")
    print(f"Endpoint: {endpoint}")
    print(f"Bucket: {bucket_name}")
    print("-" * 50)
    
    try:
        # 1. Conectar ao MinIO
        client = Minio(
            endpoint,
            access_key=access_key,
            secret_key=secret_key,
            secure=False
        )
        
        print("✅ Conexão com MinIO estabelecida!")
        
        # 2. Verificar se bucket existe
        if client.bucket_exists(bucket_name):
            print(f"✅ Bucket '{bucket_name}' existe!")
        else:
            print(f"❌ Bucket '{bucket_name}' não existe!")
            return False
        
        # 3. Verificar política do bucket
        try:
            policy = client.get_bucket_policy(bucket_name)
            policy_dict = json.loads(policy)
            print("✅ Política do bucket obtida:")
            print(json.dumps(policy_dict, indent=2))
            
            # Verificar se é pública
            is_public = False
            for statement in policy_dict.get('Statement', []):
                if (statement.get('Effect') == 'Allow' and 
                    statement.get('Principal', {}).get('AWS') == '*' and
                    's3:GetObject' in statement.get('Action', [])):
                    is_public = True
                    break
            
            if is_public:
                print("✅ Bucket está configurado como PÚBLICO!")
            else:
                print("❌ Bucket NÃO está configurado como público!")
                
        except Exception as e:
            print(f"⚠️  Não foi possível obter política do bucket: {e}")
        
        # 4. Listar objetos no bucket
        objects = list(client.list_objects(bucket_name, recursive=True))
        print(f"📁 Objetos no bucket: {len(objects)}")
        for obj in objects[:5]:  # Mostrar apenas os primeiros 5
            print(f"   - {obj.object_name}")
        
        # 5. Testar acesso público a um arquivo
        if objects:
            test_object = objects[0].object_name
            public_url = f"http://{endpoint}/{bucket_name}/{test_object}"
            print(f"🔗 Testando URL pública: {public_url}")
            
            try:
                response = requests.get(public_url, timeout=5)
                if response.status_code == 200:
                    print("✅ Acesso público FUNCIONANDO!")
                else:
                    print(f"❌ Acesso público FALHOU! Status: {response.status_code}")
            except Exception as e:
                print(f"❌ Erro ao testar acesso público: {e}")
        
        return True
        
    except S3Error as e:
        print(f"❌ Erro S3: {e}")
        return False
    except Exception as e:
        print(f"❌ Erro geral: {e}")
        return False

def fix_bucket_policy():
    """Corrige a política do bucket para torná-lo público"""
    
    endpoint = "localhost:9000"
    access_key = "minioadmin"
    secret_key = "minioadmin123"
    bucket_name = "btl-images"
    
    print("🔧 Corrigindo política do bucket...")
    
    try:
        client = Minio(
            endpoint,
            access_key=access_key,
            secret_key=secret_key,
            secure=False
        )
        
        # Política pública para leitura
        public_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {"AWS": "*"},
                    "Action": ["s3:GetObject"],
                    "Resource": [f"arn:aws:s3:::{bucket_name}/*"]
                }
            ]
        }
        
        policy_json = json.dumps(public_policy)
        client.set_bucket_policy(bucket_name, policy_json)
        
        print("✅ Política pública aplicada com sucesso!")
        return True
        
    except Exception as e:
        print(f"❌ Erro ao aplicar política: {e}")
        return False

if __name__ == '__main__':
    print("=" * 60)
    print("🧪 TESTE DE CONFIGURAÇÃO DO MINIO")
    print("=" * 60)
    
    if len(sys.argv) > 1 and sys.argv[1] == '--fix':
        print("🔧 Modo de correção ativado!")
        fix_bucket_policy()
        print("-" * 50)
    
    success = test_minio_connection()
    
    print("=" * 60)
    if success:
        print("🎉 Teste concluído com sucesso!")
    else:
        print("❌ Teste falhou! Verifique a configuração.")
        print("\n💡 Para corrigir a política do bucket, execute:")
        print("   python test_minio.py --fix")
    print("=" * 60)
