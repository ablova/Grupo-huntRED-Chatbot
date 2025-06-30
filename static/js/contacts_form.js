// Gestión del formulario de contactos con validaciones y optimización
document.addEventListener('DOMContentLoaded', function() {
    const contactsForm = document.getElementById('contactsForm');
    const cancelBtn = document.getElementById('cancelContactsForm');
    const addInviteeBtn = document.getElementById('addInviteeBtn');
    let inviteeCount = 0;

    // Validación del formulario
    if (contactsForm) {
        contactsForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const formData = new FormData(contactsForm);
            // Validaciones básicas
            let isValid = true;
            const requiredFields = ['signer', 'payment_responsible', 'fiscal_responsible', 'process_responsible'];
            requiredFields.forEach(field => {
                if (!formData.get(field)) {
                    isValid = false;
                    const input = contactsForm.querySelector(`[name="${field}"]`);
                    if (input) input.classList.add('border-red-500');
                }
            });
            if (!isValid) {
                showToast('Por favor, complete todos los campos requeridos.', 'error');
                return;
            }
            // Enviar datos al backend
            fetch(contactsForm.action, {
                method: 'POST',
                headers: { 'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value },
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    showToast('Contactos actualizados exitosamente.', 'success');
                    updateContactsSummary(data.contacts);
                } else {
                    showToast(data.message || 'Error al actualizar contactos.', 'error');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                showToast('Error al procesar la solicitud.', 'error');
            });
        });
    }
    // Cancelar edición
    if (cancelBtn) {
        cancelBtn.addEventListener('click', function() {
            contactsForm.reset();
            showToast('Edición cancelada.', 'info');
        });
    }
    // Añadir invitados adicionales
    if (addInviteeBtn) {
        addInviteeBtn.addEventListener('click', function() {
            inviteeCount++;
            const container = document.getElementById('extraInvitees');
            const div = document.createElement('div');
            div.className = 'flex gap-2 mt-2';
            div.innerHTML = `
                <input type="text" name="extra_invitee_name_${inviteeCount}" placeholder="Nombre" class="form-input block w-1/2 border-gray-300 rounded" required>
                <input type="email" name="extra_invitee_email_${inviteeCount}" placeholder="Email" class="form-input block w-1/2 border-gray-300 rounded" required>
            `;
            container.appendChild(div);
        });
    }
    // Función para mostrar notificaciones
    function showToast(message, type = 'success') {
        const toast = document.createElement('div');
        const bgColor = type === 'success' ? 'bg-green-500' : type === 'error' ? 'bg-red-500' : 'bg-blue-500';
        toast.className = `fixed bottom-4 right-4 ${bgColor} text-white px-6 py-3 rounded-lg shadow-lg animate-fade-in`;
        toast.innerHTML = `
            <div class="flex items-center">
                <i class="fas ${type === 'success' ? 'fa-check-circle' : 'fa-exclamation-circle'} mr-2"></i>
                <span>${message}</span>
            </div>
        `;
        document.body.appendChild(toast);
        setTimeout(() => {
            toast.classList.add('opacity-0', 'transition-opacity', 'duration-300');
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    }
    // Actualizar resumen de contactos
    function updateContactsSummary(contacts) {
        const table = document.querySelector('#panel-contacts table tbody');
        if (table) {
            table.innerHTML = `
                <tr>
                    <td class="p-3 text-sm text-gray-700">Firmante de propuesta</td>
                    <td class="p-3 text-sm text-gray-700">${contacts.signer.nombre} (${contacts.signer.company_email})</td>
                </tr>
                <tr>
                    <td class="p-3 text-sm text-gray-700">Responsable de pagos</td>
                    <td class="p-3 text-sm text-gray-700">${contacts.payment_responsible.nombre} (${contacts.payment_responsible.company_email})</td>
                </tr>
                <tr>
                    <td class="p-3 text-sm text-gray-700">Responsable fiscal</td>
                    <td class="p-3 text-sm text-gray-700">${contacts.fiscal_responsible.nombre} (${contacts.fiscal_responsible.company_email})</td>
                </tr>
                <tr>
                    <td class="p-3 text-sm text-gray-700">Responsable del proceso</td>
                    <td class="p-3 text-sm text-gray-700">${contacts.process_responsible.nombre} (${contacts.process_responsible.company_email})</td>
                </tr>
                <tr>
                    <td class="p-3 text-sm text-gray-700">Invitados a reportes</td>
                    <td class="p-3 text-sm text-gray-700">${contacts.report_invitees.map(p => `${p.nombre} (${p.company_email})`).join(', ') || 'No hay invitados definidos.'}</td>
                </tr>
                <tr>
                    <td class="p-3 text-sm text-gray-700">Preferencias de notificación</td>
                    <td class="p-3 text-sm text-gray-700"><pre class="text-xs bg-gray-100 p-2 rounded">${contacts.notification_preferences || 'No definidas.'}</pre></td>
                </tr>
            `;
        }
    }
}); 