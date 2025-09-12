/**
 * BTL Password Validator
 * Valida senhas com critérios de segurança e feedback visual
 */

// Configuração de requisitos de senha
const PASSWORD_REQUIREMENTS = {
    minLength: 8,
    maxLength: 128,
    requireUppercase: true,
    requireLowercase: true,
    requireNumbers: true,
    requireSpecialChars: true,
    specialChars: '!@#$%^&*()_+-=[]{}|;:,.<>?'
};

// Mensagens de validação
const MESSAGES = {
    length: `Deve ter entre ${PASSWORD_REQUIREMENTS.minLength} e ${PASSWORD_REQUIREMENTS.maxLength} caracteres`,
    uppercase: 'Deve conter pelo menos uma letra maiúscula (A-Z)',
    lowercase: 'Deve conter pelo menos uma letra minúscula (a-z)', 
    numbers: 'Deve conter pelo menos um número (0-9)',
    specialChars: `Deve conter pelo menos um caractere especial (${PASSWORD_REQUIREMENTS.specialChars})`,
    strong: 'Senha forte! ✓',
    weak: 'Senha muito fraca',
    medium: 'Senha razoável, mas pode melhorar'
};

/**
 * Valida uma senha com base nos critérios definidos
 * @param {string} password - A senha a ser validada
 * @returns {object} - Resultado da validação
 */
function validatePassword(password) {
    const validation = {
        isValid: true,
        errors: [],
        warnings: [],
        strength: 0,
        strengthLabel: ''
    };

    // Verificar comprimento
    if (password.length < PASSWORD_REQUIREMENTS.minLength || password.length > PASSWORD_REQUIREMENTS.maxLength) {
        validation.isValid = false;
        validation.errors.push(MESSAGES.length);
    } else {
        validation.strength += 20;
    }

    // Verificar letra maiúscula
    if (PASSWORD_REQUIREMENTS.requireUppercase && !/[A-Z]/.test(password)) {
        validation.isValid = false;
        validation.errors.push(MESSAGES.uppercase);
    } else if (/[A-Z]/.test(password)) {
        validation.strength += 20;
    }

    // Verificar letra minúscula
    if (PASSWORD_REQUIREMENTS.requireLowercase && !/[a-z]/.test(password)) {
        validation.isValid = false;
        validation.errors.push(MESSAGES.lowercase);
    } else if (/[a-z]/.test(password)) {
        validation.strength += 20;
    }

    // Verificar números
    if (PASSWORD_REQUIREMENTS.requireNumbers && !/[0-9]/.test(password)) {
        validation.isValid = false;
        validation.errors.push(MESSAGES.numbers);
    } else if (/[0-9]/.test(password)) {
        validation.strength += 20;
    }

    // Verificar caracteres especiais
    const specialCharsRegex = new RegExp(`[${PASSWORD_REQUIREMENTS.specialChars.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}]`);
    if (PASSWORD_REQUIREMENTS.requireSpecialChars && !specialCharsRegex.test(password)) {
        validation.isValid = false;
        validation.errors.push(MESSAGES.specialChars);
    } else if (specialCharsRegex.test(password)) {
        validation.strength += 20;
    }

    // Determinar força da senha
    if (validation.strength >= 80) {
        validation.strengthLabel = 'Forte';
    } else if (validation.strength >= 60) {
        validation.strengthLabel = 'Média';
    } else {
        validation.strengthLabel = 'Fraca';
    }

    return validation;
}

/**
 * Cria o HTML da barra de força da senha
 * @param {number} strength - Força da senha (0-100)
 * @param {string} label - Rótulo da força
 * @returns {string} - HTML da barra de força
 */
function createStrengthBar(strength, label) {
    let colorClass = 'bg-danger';
    if (strength >= 80) colorClass = 'bg-success';
    else if (strength >= 60) colorClass = 'bg-warning';

    return `
        <div class="password-strength mt-2">
            <div class="d-flex justify-content-between">
                <small class="text-muted">Força da senha:</small>
                <small class="font-weight-bold ${strength >= 80 ? 'text-success' : strength >= 60 ? 'text-warning' : 'text-danger'}">${label}</small>
            </div>
            <div class="progress mt-1" style="height: 4px;">
                <div class="progress-bar ${colorClass}" style="width: ${strength}%"></div>
            </div>
        </div>
    `;
}

/**
 * Cria o HTML da lista de requisitos
 * @param {object} validation - Resultado da validação
 * @returns {string} - HTML da lista de requisitos
 */
function createRequirementsList(validation) {
    const requirements = [
        { text: MESSAGES.length, valid: validation.errors.indexOf(MESSAGES.length) === -1 },
        { text: MESSAGES.uppercase, valid: validation.errors.indexOf(MESSAGES.uppercase) === -1 },
        { text: MESSAGES.lowercase, valid: validation.errors.indexOf(MESSAGES.lowercase) === -1 },
        { text: MESSAGES.numbers, valid: validation.errors.indexOf(MESSAGES.numbers) === -1 },
        { text: MESSAGES.specialChars, valid: validation.errors.indexOf(MESSAGES.specialChars) === -1 }
    ];

    let html = '<div class="password-requirements mt-2"><small class="text-muted">Requisitos:</small><ul class="list-unstyled mt-1">';
    
    requirements.forEach(req => {
        const icon = req.valid ? '<i class="fas fa-check text-success"></i>' : '<i class="fas fa-times text-danger"></i>';
        const textClass = req.valid ? 'text-success' : 'text-muted';
        html += `<li class="small ${textClass}">${icon} ${req.text}</li>`;
    });
    
    html += '</ul></div>';
    return html;
}

/**
 * Inicializa o validador de senha para um campo específico
 * @param {string} passwordFieldId - ID do campo de senha
 * @param {string} containerId - ID do container onde mostrar feedback (opcional)
 */
function initPasswordValidator(passwordFieldId, containerId = null) {
    const passwordField = document.getElementById(passwordFieldId);
    if (!passwordField) {
        console.error(`Campo de senha com ID '${passwordFieldId}' não encontrado`);
        return;
    }

    // Criar container de feedback se não especificado
    if (!containerId) {
        containerId = passwordFieldId + '-feedback';
        const feedbackDiv = document.createElement('div');
        feedbackDiv.id = containerId;
        passwordField.parentNode.appendChild(feedbackDiv);
    }

    const feedbackContainer = document.getElementById(containerId);
    if (!feedbackContainer) {
        console.error(`Container de feedback com ID '${containerId}' não encontrado`);
        return;
    }

    // Adicionar atributos HTML5 para validação básica
    passwordField.setAttribute('minlength', PASSWORD_REQUIREMENTS.minLength);
    passwordField.setAttribute('maxlength', PASSWORD_REQUIREMENTS.maxLength);
    
    // Criar padrão regex para validação HTML5
    const pattern = `^(?=.*[a-z])(?=.*[A-Z])(?=.*\\d)(?=.*[${PASSWORD_REQUIREMENTS.specialChars.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}]).{${PASSWORD_REQUIREMENTS.minLength},${PASSWORD_REQUIREMENTS.maxLength}}$`;
    passwordField.setAttribute('pattern', pattern);
    passwordField.setAttribute('title', 'A senha deve conter pelo menos 8 caracteres, incluindo maiúsculas, minúsculas, números e caracteres especiais');

    // Event listener para validação em tempo real
    passwordField.addEventListener('input', function() {
        const password = this.value;
        const validation = validatePassword(password);
        
        // Atualizar feedback visual
        let feedbackHTML = '';
        
        if (password.length > 0) {
            feedbackHTML += createStrengthBar(validation.strength, validation.strengthLabel);
            feedbackHTML += createRequirementsList(validation);
        }
        
        feedbackContainer.innerHTML = feedbackHTML;
        
        // Atualizar classe do campo
        passwordField.classList.remove('is-valid', 'is-invalid');
        if (password.length > 0) {
            if (validation.isValid) {
                passwordField.classList.add('is-valid');
            } else {
                passwordField.classList.add('is-invalid');
            }
        }
    });

    // Validação no submit do formulário
    const form = passwordField.closest('form');
    if (form) {
        form.addEventListener('submit', function(event) {
            const password = passwordField.value;
            const validation = validatePassword(password);
            
            if (!validation.isValid) {
                event.preventDefault();
                event.stopPropagation();
                
                // Mostrar erro
                passwordField.classList.add('is-invalid');
                feedbackContainer.innerHTML = createRequirementsList(validation);
                
                // Focar no campo
                passwordField.focus();
                
                // Mostrar alerta
                alert('Por favor, corrija os erros na senha antes de continuar.');
            }
        });
    }
}

// Inicialização automática quando o DOM estiver pronto
document.addEventListener('DOMContentLoaded', function() {
    // Procurar campos de senha automaticamente
    const passwordFields = document.querySelectorAll('input[type="password"]');
    passwordFields.forEach(field => {
        if (field.name === 'password' || field.id === 'password') {
            initPasswordValidator(field.id);
        }
    });
});
