export type ServiceItem = {
  id: string;
  title: string;
  description: string;
};

export const services: ServiceItem[] = [
  { id: 'training', title: 'Обучение', description: 'Подготовка и аттестация персонала по программам ПБ.' },
  { id: 'audit', title: 'Аудит', description: 'Комплексная диагностика системы безопасности и рисков.' },
  { id: 'documentation', title: 'Документация', description: 'Разработка регламентов, инструкций и обязательной отчетности.' },
  { id: 'outsourcing', title: 'Аутсорсинг', description: 'Передача функций специалиста по ПБ на внешнюю команду.' },
  { id: 'inspection-support', title: 'Сопровождение проверок', description: 'Подготовка к проверкам Ростехнадзора и сопровождение инспекций.' },
  { id: 'risk-assessment', title: 'Оценка рисков', description: 'Идентификация, приоритизация и план снижения производственных рисков.' }
];
