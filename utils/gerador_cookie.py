#!/usr/bin/env python3
"""
Gerador de Cookie Simples
Gera cookies seguros para autenticação e sessões
"""

import secrets
import string
import base64
import hashlib
import time
from datetime import datetime, timedelta

class CookieGenerator:
    """Gerador de cookies seguros"""
    
    def __init__(self, length=32):
        """
        Inicializa o gerador de cookies
        
        Args:
            length (int): Tamanho do cookie em caracteres (padrão: 32)
        """
        self.length = length
        self.charset = string.ascii_letters + string.digits + '+/'
    
    def generate_simple(self):
        """
        Gera um cookie simples usando caracteres alfanuméricos e símbolos
        
        Returns:
            str: Cookie gerado
        """
        return ''.join(secrets.choice(self.charset) for _ in range(self.length))
    
    def generate_base64(self):
        """
        Gera um cookie usando base64 encoding
        
        Returns:
            str: Cookie em base64
        """
        # Gera bytes aleatórios
        random_bytes = secrets.token_bytes(self.length // 2)
        # Converte para base64 e remove padding
        return base64.b64encode(random_bytes).decode('utf-8').rstrip('=')
    
    def generate_hex(self):
        """
        Gera um cookie em hexadecimal
        
        Returns:
            str: Cookie em hex
        """
        return secrets.token_hex(self.length // 2)
    
    def generate_with_timestamp(self):
        """
        Gera um cookie que inclui timestamp para expiração
        
        Returns:
            str: Cookie com timestamp
        """
        # Gera parte aleatória
        random_part = secrets.token_hex(16)
        # Adiciona timestamp
        timestamp = str(int(time.time()))
        # Combina e faz hash
        combined = f"{random_part}{timestamp}"
        return hashlib.sha256(combined.encode()).hexdigest()
    
    def generate_session_id(self):
        """
        Gera um ID de sessão similar ao exemplo fornecido
        
        Returns:
            str: ID de sessão
        """
        # Gera 32 bytes aleatórios
        random_bytes = secrets.token_bytes(32)
        # Converte para base64 e remove padding
        return base64.b64encode(random_bytes).decode('utf-8').rstrip('=')
    
    def generate_multiple(self, count=5, method='simple'):
        """
        Gera múltiplos cookies
        
        Args:
            count (int): Número de cookies a gerar
            method (str): Método de geração ('simple', 'base64', 'hex', 'timestamp', 'session')
        
        Returns:
            list: Lista de cookies gerados
        """
        methods = {
            'simple': self.generate_simple,
            'base64': self.generate_base64,
            'hex': self.generate_hex,
            'timestamp': self.generate_with_timestamp,
            'session': self.generate_session_id
        }
        
        if method not in methods:
            raise ValueError(f"Método '{method}' não suportado. Use: {list(methods.keys())}")
        
        return [methods[method]() for _ in range(count)]

def main():
    """Função principal - Interface de linha de comando"""
    print("🍪 Gerador de Cookie Simples")
    print("=" * 40)
    
    # Configurações
    length = 32
    generator = CookieGenerator(length)
    
    while True:
        print("\n📋 Opções disponíveis:")
        print("1. Gerar cookie simples")
        print("2. Gerar cookie base64")
        print("3. Gerar cookie hexadecimal")
        print("4. Gerar cookie com timestamp")
        print("5. Gerar ID de sessão (como exemplo)")
        print("6. Gerar múltiplos cookies")
        print("7. Configurar tamanho")
        print("8. Sair")
        
        choice = input("\nEscolha uma opção (1-8): ").strip()
        
        if choice == '1':
            cookie = generator.generate_simple()
            print(f"\n✅ Cookie simples: {cookie}")
            
        elif choice == '2':
            cookie = generator.generate_base64()
            print(f"\n✅ Cookie base64: {cookie}")
            
        elif choice == '3':
            cookie = generator.generate_hex()
            print(f"\n✅ Cookie hex: {cookie}")
            
        elif choice == '4':
            cookie = generator.generate_with_timestamp()
            print(f"\n✅ Cookie com timestamp: {cookie}")
            
        elif choice == '5':
            cookie = generator.generate_session_id()
            print(f"\n✅ ID de sessão: {cookie}")
            print(f"   (Similar ao exemplo: UOiaDrpnOcHc4elcu6i8/kyv8qoXPXDe277hurcu8r3=)")
            
        elif choice == '6':
            method = input("Método (simple/base64/hex/timestamp/session): ").strip().lower()
            count = int(input("Quantidade: ") or "5")
            cookies = generator.generate_multiple(count, method)
            print(f"\n✅ {count} cookies gerados:")
            for i, cookie in enumerate(cookies, 1):
                print(f"   {i}. {cookie}")
                
        elif choice == '7':
            new_length = int(input(f"Novo tamanho (atual: {length}): ") or str(length))
            generator = CookieGenerator(new_length)
            length = new_length
            print(f"✅ Tamanho alterado para {length}")
            
        elif choice == '8':
            print("👋 Até logo!")
            break
            
        else:
            print("❌ Opção inválida!")
        
        # Pergunta se quer copiar
        if choice in ['1', '2', '3', '4', '5']:
            copy_choice = input("\n📋 Copiar para área de transferência? (s/n): ").strip().lower()
            if copy_choice == 's':
                try:
                    import pyperclip
                    pyperclip.copy(cookie)
                    print("✅ Copiado para área de transferência!")
                except ImportError:
                    print("⚠️  pyperclip não instalado. Instale com: pip install pyperclip")

if __name__ == "__main__":
    main()
