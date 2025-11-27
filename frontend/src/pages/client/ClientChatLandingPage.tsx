import { cardClass, sectionTitleClass, subtleButtonClass } from '../../components/ui';
import { Link } from 'react-router-dom';

const ClientChatLandingPage = () => (
  <div className={cardClass}>
    <h3 className={sectionTitleClass}>Чаты и помощник</h3>
    <p className="mt-2 text-sm text-slate-700">
      Выберите чат слева или создайте новый запрос. Можно также перейти в заказы и открыть чат из
      деталей заказа.
    </p>
    <div className="mt-3 flex gap-2">
      <Link className={subtleButtonClass} to="/client/orders">
        Мои заказы
      </Link>
      <Link className={subtleButtonClass} to="/client/orders/new">
        Создать заказ
      </Link>
    </div>
  </div>
);

export default ClientChatLandingPage;
