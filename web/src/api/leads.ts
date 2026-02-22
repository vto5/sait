export type LeadPayload = {
  name: string;
  company: string;
  phone: string;
  email: string;
  serviceType: string;
};

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000';

export const submitLead = async (payload: LeadPayload) => {
  const response = await fetch(`${API_BASE_URL}/api/leads`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(payload)
  });

  if (!response.ok) {
    throw new Error('Не удалось отправить заявку. Попробуйте позже.');
  }

  return response.json();
};
