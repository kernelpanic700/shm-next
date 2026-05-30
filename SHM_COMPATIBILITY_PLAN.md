# SHM compatibility plan

Цель: постепенно довести `shm-next` до функциональной совместимости с SHM, сохранив текущую архитектуру DDD/Litestar/PostgreSQL.

## Источники

- Документация SHM: https://docs.myshm.ru/docs/
- GitHub SHM: https://github.com/danuk/shm

## Ключевая модель SHM

SHM — биллинг разовых и периодических услуг с событиями и внешними действиями. Он не предназначен для учета потребленных ресурсов вроде трафика, минут или звонков.

Базовый цикл:

1. Администратор создает услуги с ценой, периодом и правилами.
2. Клиенту оказывается услуга.
3. Биллинг списывает платежи/бонусы, продлевает или завершает услуги.
4. События услуги создают внешние действия через spool/action queue.

## Gap map

### Уже есть в shm-next

- Абоненты, платежи, списания, бонусы, скидки.
- User services, service statuses.
- Event bus и spool-задачи.
- Admin/client UI основы.
- Базовый billing engine.

### Нужно добавить/расширить

- Каталог услуг SHM: `category`, `cost`, `period_cost`, `next`, `children`, `allow_to_order`, `pay_in_credit`, `pay_always`, `config`.
- Пользовательские услуги как оказанные услуги с `expire_at`, SHM status lifecycle и индивидуальной ценой/периодом.
- Режимы расчета SHM:
  - фиксированные 30 дней в месяце;
  - календарный расчет;
  - расчет по последнему дню месяца.
- Заказ услуги:
  - проверка доступности;
  - расчет цены `cost * qnt - скидки - бонусы`;
  - поддержка кредита;
  - создание дочерних услуг;
  - генерация событий.
- Продление услуги:
  - автопродление;
  - `next = -1` удалить;
  - переход на следующую услугу;
  - блокировка при нехватке средств.
- Досрочное удаление:
  - расчет фактически использованной части периода;
  - возврат остатка;
  - события отключения.
- События услуг и команды:
  - category-based event actions;
  - retry/backoff;
  - DLQ/audit.
- API/admin/client:
  - управление каталогом услуг;
  - заказ доступных услуг;
  - история платежей, бонусов, списаний;
  - настройка событий и команд.

## Implementation phases

1. **Billing core compatibility** — done
   - SHM period parser.
   - SHM billing modes.
   - Order/refund calculation with discounts and bonuses.
   - Unit tests.

2. **Domain model and migrations** — in progress
   - Service catalog entity/table.
   - Extend user services with `expire_at`, `period_cost`, `next_service_id`, `parent_id`, `quantity`, `pay_*` flags.
   - Migration and repositories.

3. **Use cases** — in progress
   - Order service.
   - Renew service.
   - Stop/delete service with refund.
   - Block/unblock on insufficient funds.

4. **Events and actions** — in progress
   - Service event definitions.
   - Event action rules.
   - Spool integration and retry behavior.

5. **API and UI**
   - Admin service catalog.
   - Client available services/order flow.
   - Billing history screens.
