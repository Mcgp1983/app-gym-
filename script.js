const plans = [
  {
    id: 'day-pass',
    name: 'Acesso Diário',
    description: 'Ideal para quem quer experimentar ou está de passagem pela cidade.',
    price: 39.9,
    badge: 'Popular',
    features: ['Acesso ilimitado por 24h', 'Locker incluso', 'Wi-Fi premium e área lounge'],
  },
  {
    id: 'week-pass',
    name: 'Plano Semanal',
    description: 'Treine a semana inteira com flexibilidade total de horários.',
    price: 149.9,
    features: [
      'Acesso 7 dias consecutivos',
      '2 convidados gratuitos',
      'Avaliação física inicial',
    ],
  },
  {
    id: 'month-pass',
    name: 'Plano Mensal Flex',
    description: 'Perfeito para quem precisa de autonomia com suporte completo da equipe.',
    price: 229.9,
    badge: 'Melhor custo-benefício',
    features: [
      'Acesso ilimitado 30 dias',
      'Consultoria com treinador',
      'Aulas coletivas inclusas',
      'Aplicativo com treinos personalizados',
    ],
  },
];

const plansGrid = document.getElementById('plans-grid');
const modal = document.getElementById('purchase-modal');
const modalTitle = document.getElementById('modal-plan-title');
const modalPrice = document.getElementById('modal-plan-price');
const modalFeatures = document.getElementById('modal-plan-features');
const checkoutForm = document.getElementById('checkout-form');
const purchaseResult = document.getElementById('purchase-result');
const purchaseDetails = document.getElementById('purchase-details');
const purchaseLoading = document.getElementById('purchase-loading');
const qrCanvas = document.getElementById('qr-code-canvas');
const newPurchaseBtn = document.getElementById('new-purchase');
const startDateInput = document.getElementById('start-date');

let selectedPlan;

function formatPrice(value) {
  return value.toLocaleString('pt-BR', {
    style: 'currency',
    currency: 'BRL',
  });
}

function createPlanCard(plan) {
  const card = document.createElement('article');
  card.className = 'plan-card';
  if (plan.badge) {
    card.classList.add('plan-card--highlight');
  }

  const badge = plan.badge
    ? `<span class="plan-card__badge">${plan.badge}</span>`
    : '';

  card.innerHTML = `
    ${badge}
    <h3>${plan.name}</h3>
    <p class="plan-card__price">${formatPrice(plan.price)} <span>/ acesso</span></p>
    <p>${plan.description}</p>
    <ul>${plan.features.map((feature) => `<li>${feature}</li>`).join('')}</ul>
    <button class="btn btn--primary" data-plan="${plan.id}">Comprar agora</button>
  `;

  return card;
}

function renderPlans() {
  plans.forEach((plan) => {
    plansGrid.appendChild(createPlanCard(plan));
  });
}

function openModal(planId) {
  selectedPlan = plans.find((plan) => plan.id === planId);
  if (!selectedPlan) return;

  modalTitle.textContent = selectedPlan.name;
  modalPrice.textContent = formatPrice(selectedPlan.price);
  modalFeatures.innerHTML = selectedPlan.features
    .map((feature) => `<li>${feature}</li>`)
    .join('');
  checkoutForm.reset();
  const today = new Date().toISOString().split('T')[0];
  startDateInput.min = today;
  startDateInput.value = today;

  purchaseResult.hidden = true;
  purchaseLoading.hidden = true;
  checkoutForm.hidden = false;

  modal.setAttribute('aria-hidden', 'false');
  modal.classList.add('is-visible');
  const firstInput = checkoutForm.querySelector('input');
  window.setTimeout(() => firstInput?.focus(), 150);
}

function closeModal() {
  modal.classList.remove('is-visible');
  modal.setAttribute('aria-hidden', 'true');
  checkoutForm.reset();
  purchaseResult.hidden = true;
  purchaseLoading.hidden = true;
  checkoutForm.hidden = false;
}

function simulatePayment(formData) {
  return new Promise((resolve) => {
    setTimeout(() => {
      const purchaseId = Math.random().toString(36).substring(2, 10).toUpperCase();
      resolve({
        purchaseId,
        name: formData.get('name'),
        email: formData.get('email'),
        phone: formData.get('phone'),
        startDate: formData.get('startDate'),
      });
    }, 1600);
  });
}

function buildPayload(details) {
  return JSON.stringify({
    id: details.purchaseId,
    plan: selectedPlan.id,
    start: details.startDate,
    name: details.name,
  });
}

function generateQRCode(payload) {
  if (!window.QRCode) {
    purchaseDetails.innerHTML =
      '<p class="error">Não foi possível gerar o QR Code. Atualize a página e tente novamente.</p>';
    return;
  }

  QRCode.toCanvas(
    qrCanvas,
    payload,
    {
      width: 220,
      margin: 1,
      color: {
        dark: '#14151f',
        light: '#ffffff',
      },
    },
    (error) => {
      if (error) {
        purchaseDetails.innerHTML =
          '<p class="error">Houve um problema ao gerar o QR Code. Tente novamente.</p>';
      }
    }
  );
}

function showResult(details) {
  const payload = buildPayload(details);
  generateQRCode(payload);
  purchaseDetails.innerHTML = `
    <dl>
      <div>
        <dt>Número do pedido</dt>
        <dd>${details.purchaseId}</dd>
      </div>
      <div>
        <dt>Plano</dt>
        <dd>${selectedPlan.name}</dd>
      </div>
      <div>
        <dt>Início do acesso</dt>
        <dd>${new Date(details.startDate).toLocaleDateString('pt-BR')}</dd>
      </div>
      <div>
        <dt>Enviado para</dt>
        <dd>${details.email}</dd>
      </div>
    </dl>
  `;

  purchaseLoading.hidden = true;
  purchaseResult.hidden = false;
}

function handlePurchase(event) {
  event.preventDefault();
  if (!selectedPlan) return;

  const formData = new FormData(checkoutForm);
  checkoutForm.hidden = true;
  purchaseLoading.hidden = false;

  simulatePayment(formData).then((details) => {
    showResult(details);
  });
}

function handleClick(event) {
  const button = event.target.closest('button[data-plan]');
  if (!button) return;
  openModal(button.dataset.plan);
}

function handleModalClose(event) {
  if (event.target.dataset.close === 'true') {
    closeModal();
  }
}

function init() {
  renderPlans();
  plansGrid.addEventListener('click', handleClick);
  modal.addEventListener('click', handleModalClose);
  checkoutForm.addEventListener('submit', handlePurchase);
  newPurchaseBtn.addEventListener('click', closeModal);
  document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape' && modal.classList.contains('is-visible')) {
      closeModal();
    }
  });
}

init();
