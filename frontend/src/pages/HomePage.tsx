import { Link } from 'react-router-dom';
import { cardClass, sectionTitleClass, subtleButtonClass } from '../components/ui';

const HomePage = () => {
  return (
    <div className="grid gap-4 lg:grid-cols-3">
      <div className={cardClass}>
        <h2 className={sectionTitleClass}>Быстрый старт</h2>
        <p className="mt-2 text-sm text-slate-700">
          Авторизуйтесь и переходите в нужный кабинет, чтобы проверить основные сценарии работы с
          заказами, файлами, планом и чатами.
        </p>
        <div className="mt-3 flex flex-wrap gap-2">
          <Link to="/auth" className={subtleButtonClass}>
            Авторизация
          </Link>
          <Link to="/client" className={subtleButtonClass}>
            Кабинет клиента
          </Link>
          <Link to="/executor" className={subtleButtonClass}>
            Кабинет исполнителя
          </Link>
          <Link to="/admin" className={subtleButtonClass}>
            Админка
          </Link>
        </div>
      </div>
      <div className={cardClass}>
        <h2 className={sectionTitleClass}>Основные проверки</h2>
        <ul className="mt-2 list-disc pl-5 text-sm text-slate-700">
          <li>Каталог услуг, округов и типов домов.</li>
          <li>Создание, просмотр и файлы заказа.</li>
          <li>План заказа, история статусов, чат с AI.</li>
          <li>Задачи исполнителя и календарь.</li>
          <li>Админ: пользователи, исполнители, заказы, справочники.</li>
        </ul>
      </div>
      <div className={cardClass}>
        <h2 className={sectionTitleClass}>Подсказки</h2>
        <ul className="mt-2 list-disc pl-5 text-sm text-slate-700">
          <li>API префикс уже настроен (/api/v1).</li>
          <li>Все роли определяются по /auth/me.</li>
          <li>Если нет доступа, убедитесь в корректности роли.</li>
        </ul>
      </div>
    </div>
  );
};

export default HomePage;
