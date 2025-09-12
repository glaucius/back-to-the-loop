"""
BTL Password Service
Serviço de validação de senhas com critérios de segurança
"""

import re
from typing import Dict, List, Tuple

class PasswordService:
    """Serviço para validação e gerenciamento de senhas"""
    
    def __init__(self):
        # Configuração de requisitos de senha
        self.config = {
            'min_length': 8,
            'max_length': 128,
            'require_uppercase': True,
            'require_lowercase': True,
            'require_numbers': True,
            'require_special_chars': True,
            'special_chars': '!@#$%^&*()_+-=[]{}|;:,.<>?'
        }
        
        # Mensagens de erro em português
        self.error_messages = {
            'length': f'A senha deve ter entre {self.config["min_length"]} e {self.config["max_length"]} caracteres',
            'uppercase': 'A senha deve conter pelo menos uma letra maiúscula (A-Z)',
            'lowercase': 'A senha deve conter pelo menos uma letra minúscula (a-z)',
            'numbers': 'A senha deve conter pelo menos um número (0-9)',
            'special_chars': f'A senha deve conter pelo menos um caractere especial ({self.config["special_chars"]})',
            'common_password': 'Esta senha é muito comum. Escolha uma senha mais segura.',
            'sequential': 'A senha não deve conter sequências óbvias de caracteres',
            'repeated': 'A senha não deve conter muitos caracteres repetidos',
            'contains_username': 'A senha não deve conter o nome de usuário',
            'contains_email': 'A senha não deve conter partes do email'
        }
        
        # Lista de senhas comuns que devem ser rejeitadas
        self.common_passwords = {
            '12345678', 'password', '123456789', 'qwerty', 'abc123', 'password123', 
            'admin', 'admin123', 'user', 'test', 'guest', '87654321', 'qwerty123',
            'password1', '123123123', 'senha', 'senha123', 'administrador', 'usuario',
            'backyard', 'btl123', 'corrida', 'ultramaratona', 'atleta123'
        }
    
    def validate_password(self, password: str, username: str = None, email: str = None) -> Dict:
        """
        Valida uma senha com base nos critérios de segurança
        
        Args:
            password: A senha a ser validada
            username: Nome de usuário (opcional)
            email: Email (opcional)
        
        Returns:
            Dict: Resultado da validação com estrutura:
            {
                'is_valid': bool,
                'errors': List[str],
                'warnings': List[str],
                'strength_score': int (0-100),
                'strength_label': str
            }
        """
        result = {
            'is_valid': True,
            'errors': [],
            'warnings': [],
            'strength_score': 0,
            'strength_label': ''
        }
        
        if not password:
            result['is_valid'] = False
            result['errors'].append("A senha é obrigatória")
            return result
        
        # 1. Verificar comprimento
        if len(password) < self.config['min_length'] or len(password) > self.config['max_length']:
            result['is_valid'] = False
            result['errors'].append(self.error_messages['length'])
        else:
            result['strength_score'] += 20
        
        # 2. Verificar letra maiúscula
        if self.config['require_uppercase']:
            if not re.search(r'[A-Z]', password):
                result['is_valid'] = False
                result['errors'].append(self.error_messages['uppercase'])
            else:
                result['strength_score'] += 15
        
        # 3. Verificar letra minúscula
        if self.config['require_lowercase']:
            if not re.search(r'[a-z]', password):
                result['is_valid'] = False
                result['errors'].append(self.error_messages['lowercase'])
            else:
                result['strength_score'] += 15
        
        # 4. Verificar números
        if self.config['require_numbers']:
            if not re.search(r'[0-9]', password):
                result['is_valid'] = False
                result['errors'].append(self.error_messages['numbers'])
            else:
                result['strength_score'] += 15
        
        # 5. Verificar caracteres especiais
        if self.config['require_special_chars']:
            special_chars_escaped = re.escape(self.config['special_chars'])
            if not re.search(f'[{special_chars_escaped}]', password):
                result['is_valid'] = False
                result['errors'].append(self.error_messages['special_chars'])
            else:
                result['strength_score'] += 15
        
        # 6. Verificar senhas comuns
        if password.lower() in self.common_passwords:
            result['is_valid'] = False
            result['errors'].append(self.error_messages['common_password'])
        
        # 7. Verificar se contém username ou email
        if username and len(username) > 3:
            if username.lower() in password.lower():
                result['warnings'].append(self.error_messages['contains_username'])
        
        if email and len(email) > 3:
            email_user = email.split('@')[0]
            if len(email_user) > 3 and email_user.lower() in password.lower():
                result['warnings'].append(self.error_messages['contains_email'])
        
        # 8. Verificar sequências óbvias
        if self._has_sequential_chars(password):
            result['warnings'].append(self.error_messages['sequential'])
            result['strength_score'] -= 10
        
        # 9. Verificar caracteres repetidos
        if self._has_too_many_repeated_chars(password):
            result['warnings'].append(self.error_messages['repeated'])
            result['strength_score'] -= 10
        
        # 10. Bonificações por complexidade
        if len(password) >= 12:
            result['strength_score'] += 10
        
        if self._has_mixed_case_and_special(password):
            result['strength_score'] += 10
        
        # Normalizar score (0-100)
        result['strength_score'] = max(0, min(100, result['strength_score']))
        
        # Determinar rótulo de força
        if result['strength_score'] >= 80:
            result['strength_label'] = 'Forte'
        elif result['strength_score'] >= 60:
            result['strength_label'] = 'Média'
        elif result['strength_score'] >= 40:
            result['strength_label'] = 'Fraca'
        else:
            result['strength_label'] = 'Muito Fraca'
        
        return result
    
    def get_requirements_list(self) -> List[str]:
        """Retorna lista de requisitos de senha para exibição"""
        return [
            f"Entre {self.config['min_length']} e {self.config['max_length']} caracteres",
            "Pelo menos uma letra maiúscula (A-Z)",
            "Pelo menos uma letra minúscula (a-z)",
            "Pelo menos um número (0-9)",
            f"Pelo menos um caractere especial ({self.config['special_chars']})",
            "Não deve ser uma senha comum",
            "Não deve conter seu nome de usuário ou email"
        ]
    
    def get_html_pattern(self) -> str:
        """Retorna padrão regex para validação HTML5"""
        return f"^(?=.*[a-z])(?=.*[A-Z])(?=.*\\d)(?=.*[{re.escape(self.config['special_chars'])}]).{{{self.config['min_length']},{self.config['max_length']}}}$"
    
    def get_html_attributes(self) -> Dict[str, str]:
        """Retorna atributos HTML5 para o campo de senha"""
        return {
            'minlength': str(self.config['min_length']),
            'maxlength': str(self.config['max_length']),
            'pattern': self.get_html_pattern(),
            'title': 'A senha deve conter pelo menos 8 caracteres, incluindo maiúsculas, minúsculas, números e caracteres especiais'
        }
    
    def validate_for_flask(self, password: str, **kwargs) -> Tuple[bool, List[str]]:
        """
        Função de conveniência para validação em views Flask
        
        Returns:
            Tuple[bool, List[str]]: (is_valid, error_messages)
        """
        result = self.validate_password(password, **kwargs)
        return result['is_valid'], result['errors']
    
    def _has_sequential_chars(self, password: str) -> bool:
        """Verifica se a senha contém sequências óbvias de caracteres"""
        sequences = [
            '123456', '654321', 'abcdef', 'fedcba', 'qwerty', 'asdfgh',
            '098765', 'zyxwvu', 'mnbvcx', 'poiuyt'
        ]
        
        password_lower = password.lower()
        for seq in sequences:
            if seq in password_lower:
                return True
        
        # Verificar sequências numéricas
        for i in range(len(password) - 3):
            try:
                substring = password[i:i+4]
                if substring.isdigit():
                    digits = [int(d) for d in substring]
                    # Sequência crescente ou decrescente
                    if (all(digits[j] == digits[j-1] + 1 for j in range(1, len(digits))) or
                        all(digits[j] == digits[j-1] - 1 for j in range(1, len(digits)))):
                        return True
            except:
                continue
        
        return False
    
    def _has_too_many_repeated_chars(self, password: str) -> bool:
        """Verifica se a senha tem muitos caracteres repetidos"""
        # Verificar mais de 2 caracteres iguais consecutivos
        for i in range(len(password) - 2):
            if password[i] == password[i+1] == password[i+2]:
                return True
        
        # Verificar se mais de 50% dos caracteres são iguais
        char_count = {}
        for char in password:
            char_count[char] = char_count.get(char, 0) + 1
        
        most_frequent = max(char_count.values())
        if most_frequent > len(password) * 0.5:
            return True
        
        return False
    
    def _has_mixed_case_and_special(self, password: str) -> bool:
        """Verifica se a senha tem boa mistura de tipos de caracteres"""
        has_upper = bool(re.search(r'[A-Z]', password))
        has_lower = bool(re.search(r'[a-z]', password))
        has_digit = bool(re.search(r'[0-9]', password))
        has_special = bool(re.search(f'[{re.escape(self.config["special_chars"])}]', password))
        
        return sum([has_upper, has_lower, has_digit, has_special]) >= 3
