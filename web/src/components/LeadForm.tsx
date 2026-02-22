import { FormEvent, useState } from 'react';
import { submitLead } from '../api/leads';
import { services } from '../content/services';
import { Button } from './Button';

type LeadFormState = {
  name: string;
  company: string;
  phone: string;
  email: string;
  serviceType: string;
};

const initialState: LeadFormState = {
  name: '',
  company: '',
  phone: '',
  email: '',
  serviceType: services[0].title
};

export const LeadForm = () => {
  const [form, setForm] = useState(initialState);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [loading, setLoading] = useState(false);

  const validate = () => {
    if (!form.name.trim() || !form.company.trim() || !form.phone.trim() || !form.email.trim()) {
      return 'Заполните все обязательные поля.';
    }

    const emailRe = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRe.test(form.email)) {
      return 'Введите корректный email.';
    }

    const phoneRe = /^[+\d\s()-]{7,20}$/;
    if (!phoneRe.test(form.phone)) {
      return 'Введите корректный телефон.';
    }

    return '';
  };

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError('');
    setSuccess('');

    const validationError = validate();
    if (validationError) {
      setError(validationError);
      return;
    }

    setLoading(true);
    try {
      await submitLead(form);
      setSuccess('Заявка отправлена. Мы свяжемся с вами в ближайшее время.');
      setForm(initialState);
    } catch (submitError) {
      setError(submitError instanceof Error ? submitError.message : 'Ошибка отправки.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <form className="lead-form" onSubmit={handleSubmit} noValidate>
      <h3>Оставить заявку</h3>
      <label>
        Имя
        <input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} required />
      </label>
      <label>
        Компания
        <input value={form.company} onChange={(e) => setForm({ ...form, company: e.target.value })} required />
      </label>
      <label>
        Телефон
        <input value={form.phone} onChange={(e) => setForm({ ...form, phone: e.target.value })} required />
      </label>
      <label>
        Email
        <input type="email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} required />
      </label>
      <label>
        Тип услуги
        <select value={form.serviceType} onChange={(e) => setForm({ ...form, serviceType: e.target.value })}>
          {services.map((service) => (
            <option key={service.id} value={service.title}>
              {service.title}
            </option>
          ))}
        </select>
      </label>
      <Button type="submit" disabled={loading}>
        {loading ? 'Отправка...' : 'Отправить заявку'}
      </Button>
      {error ? <p className="form-message form-message--error">{error}</p> : null}
      {success ? <p className="form-message form-message--success">{success}</p> : null}
    </form>
  );
};
