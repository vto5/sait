import { Link } from 'react-router-dom';
import { Button } from '../components/Button';
import { CaseCard } from '../components/CaseCard';
import { DocumentCard } from '../components/DocumentCard';
import { LeadForm } from '../components/LeadForm';
import { Section } from '../components/Section';
import { ServiceCard } from '../components/ServiceCard';
import { cases } from '../content/cases';
import { companyInfo } from '../content/company';
import { documents } from '../content/documents';
import { services } from '../content/services';

export const HomePage = () => {
  return (
    <main>
      <section className="hero">
        <div className="container hero__inner">
          <p className="eyebrow">{companyInfo.name}</p>
          <h1>{companyInfo.tagline}</h1>
          <p>{companyInfo.about}</p>
          <div className="hero__actions">
            <a href="#lead-form">
              <Button>Получить консультацию</Button>
            </a>
            <a href="#services">
              <Button variant="secondary">Заказать аудит</Button>
            </a>
          </div>
        </div>
      </section>

      <Section id="about" title="О компании">
        <p>{companyInfo.about}</p>
      </Section>

      <Section id="services" title="Услуги" subtitle="Решения под задачи предприятий с ОПО.">
        <div className="grid grid--services">
          {services.map((service) => (
            <ServiceCard key={service.id} {...service} />
          ))}
        </div>
      </Section>

      <Section id="why-us" title="Почему выбирают нас">
        <ul className="bullet-list">
          {companyInfo.whyChooseUs.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      </Section>

      <Section id="cases" title="Кейсы и результаты">
        <div className="grid grid--cases">
          {cases.map((item) => (
            <CaseCard key={item.id} title={item.title} result={item.result} />
          ))}
        </div>
      </Section>

      <Section id="documents" title="Лицензии и документы">
        <div className="grid grid--documents">
          {documents.map((document) => (
            <DocumentCard key={document.id} title={document.title} fileUrl={document.fileUrl} />
          ))}
        </div>
      </Section>

      <Section id="lead-form" title="Форма заявки">
        <LeadForm />
      </Section>

      <Section id="contacts" title="Контакты">
        <div className="contacts">
          <p>
            <strong>Адрес:</strong> {companyInfo.contacts.address}
          </p>
          <p>
            <strong>Телефон:</strong> <a href={`tel:${companyInfo.contacts.phone}`}>{companyInfo.contacts.phone}</a>
          </p>
          <p>
            <strong>Email:</strong> <a href={`mailto:${companyInfo.contacts.email}`}>{companyInfo.contacts.email}</a>
          </p>
          <p>
            <strong>Реквизиты:</strong> {companyInfo.contacts.requisites}
          </p>
          <iframe
            title="Карта офиса"
            src={companyInfo.contacts.mapUrl}
            loading="lazy"
            referrerPolicy="no-referrer-when-downgrade"
          />
        </div>
      </Section>

      <footer className="container footer">
        <Link to="/blog">Блог</Link>
      </footer>
    </main>
  );
};
