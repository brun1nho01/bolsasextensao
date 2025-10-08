#!/usr/bin/env python3
"""
Script para gerar tokens JWT para scraping
Uso: python generate_jwt_token.py
"""
import os
import sys
from datetime import timedelta
from dotenv import load_dotenv

# Carrega variáveis de ambiente
load_dotenv()

# Importa o gerenciador JWT
from jwt_auth import jwt_manager

def generate_scraper_token():
    """Gera token JWT para scraping"""
    
    print("\n🔐 GERADOR DE TOKEN JWT PARA SCRAPING\n")
    print("=" * 50)
    
    # Configurações
    subject = "scraping-service"
    token_type = "scraper"
    scopes = ["scraper:run", "scraper:read", "data:write"]
    
    # Opções de expiração
    print("\nEscolha o tempo de expiração do token:")
    print("1. 1 hora (padrão)")
    print("2. 24 horas (1 dia)")
    print("3. 7 dias")
    print("4. 30 dias")
    print("5. 1 ano")
    print("6. Customizado")
    
    choice = input("\nOpção (1-6): ").strip() or "1"
    
    expires_delta = None
    if choice == "1":
        expires_delta = timedelta(hours=1)
        exp_label = "1 hora"
    elif choice == "2":
        expires_delta = timedelta(days=1)
        exp_label = "24 horas"
    elif choice == "3":
        expires_delta = timedelta(days=7)
        exp_label = "7 dias"
    elif choice == "4":
        expires_delta = timedelta(days=30)
        exp_label = "30 dias"
    elif choice == "5":
        expires_delta = timedelta(days=365)
        exp_label = "1 ano"
    elif choice == "6":
        hours = int(input("Quantas horas? "))
        expires_delta = timedelta(hours=hours)
        exp_label = f"{hours} horas"
    else:
        expires_delta = timedelta(hours=1)
        exp_label = "1 hora (padrão)"
    
    # Gera token
    token = jwt_manager.create_access_token(
        subject=subject,
        token_type=token_type,
        scopes=scopes,
        expires_delta=expires_delta
    )
    
    print("\n" + "=" * 50)
    print("\n✅ TOKEN JWT GERADO COM SUCESSO!\n")
    print(f"📋 Subject: {subject}")
    print(f"🔑 Tipo: {token_type}")
    print(f"🎫 Permissões: {', '.join(scopes)}")
    print(f"⏱️  Expira em: {exp_label}")
    print("\n" + "-" * 50)
    print("\n🔐 SEU TOKEN:\n")
    print(token)
    print("\n" + "-" * 50)
    
    print("\n📝 COMO USAR:\n")
    print("1. CURL:")
    print(f'   curl -H "Authorization: Bearer {token}" https://sua-api.com/api/scrape/start')
    print("\n2. Python requests:")
    print(f'   headers = {{"Authorization": "Bearer {token}"}}')
    print('   response = requests.post(url, headers=headers)')
    print("\n3. Variável de ambiente:")
    print(f'   export SCRAPER_JWT_TOKEN="{token}"')
    
    print("\n" + "=" * 50)
    
    # Salvar em arquivo?
    save = input("\n💾 Salvar token em arquivo? (s/N): ").strip().lower()
    if save == 's':
        filename = input("Nome do arquivo (jwt_token.txt): ").strip() or "jwt_token.txt"
        with open(filename, 'w') as f:
            f.write(token)
        print(f"\n✅ Token salvo em: {filename}")
    
    print("\n⚠️  IMPORTANTE:")
    print("   - Mantenha este token em segredo")
    print("   - Não compartilhe publicamente")
    print("   - Use HTTPS em produção")
    print("   - Gere novo token quando expirar\n")


def verify_token():
    """Verifica um token JWT existente"""
    
    print("\n🔍 VERIFICAR TOKEN JWT\n")
    print("=" * 50)
    
    token = input("\nCole o token JWT: ").strip()
    
    try:
        token_data = jwt_manager.verify_token(token)
        
        print("\n✅ TOKEN VÁLIDO!\n")
        print(f"📋 Subject: {token_data.sub}")
        print(f"🔑 Tipo: {token_data.type}")
        print(f"🎫 Permissões: {', '.join(token_data.scope)}")
        print(f"📅 Emitido em: {token_data.iat}")
        print(f"⏰ Expira em: {token_data.exp}")
        
        # Calcula tempo restante
        from datetime import datetime
        now = datetime.utcnow()
        time_left = token_data.exp - now
        
        if time_left.total_seconds() > 0:
            hours_left = time_left.total_seconds() / 3600
            print(f"⏱️  Tempo restante: {hours_left:.2f} horas")
        else:
            print("⚠️  TOKEN EXPIRADO!")
        
    except Exception as e:
        print(f"\n❌ TOKEN INVÁLIDO: {e}")
    
    print("\n" + "=" * 50 + "\n")


if __name__ == "__main__":
    print("\n" + "🔐" * 25)
    
    while True:
        print("\nESCOLHA UMA OPÇÃO:")
        print("1. Gerar novo token JWT")
        print("2. Verificar token existente")
        print("3. Sair")
        
        choice = input("\nOpção (1-3): ").strip()
        
        if choice == "1":
            generate_scraper_token()
        elif choice == "2":
            verify_token()
        elif choice == "3":
            print("\n👋 Até logo!\n")
            break
        else:
            print("\n⚠️  Opção inválida!")

