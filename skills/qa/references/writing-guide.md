# Writing Guide — Come scrivere test per categoria

Questo file è la guida operativa che l'agente segue quando scrive test.
Contiene pattern, anti-pattern, e template per ogni categoria.

---

## Regole universali (tutte le categorie)

1. **Header obbligatorio** in ogni file di test:
   ```python
   # Categoria: unit | integration | e2e | performance | a11y
   # File sorgente: src/path/to/module.py
   # Creato: YYYY-MM-DD
   # Aggiornato: YYYY-MM-DD
   ```

2. **Un test = un comportamento**, non una funzione. Il nome del test deve descrivere
   il comportamento: `test_returns_404_when_user_not_found` non `test_get_user`.

3. **Struttura AAA**: Arrange → Act → Assert. Un blocco per ciascuno, separati da riga vuota.

4. **Mai dipendenze tra test**: ogni test deve poter girare da solo in qualsiasi ordine.

5. **Mock tutto ciò che è esterno** negli unit test: database, API, filesystem, orario.

6. **Nomi file**:
   - Python: `test_<nome_modulo>.py`
   - TS/JS: `<nome_modulo>.test.ts`

---

## UNIT TEST

### Pattern Python (pytest)

```python
# Categoria: unit
# File sorgente: src/services/user_service.py
# Creato: 2024-01-15

import pytest
from unittest.mock import AsyncMock, patch
from src.services.user_service import UserService

class TestUserService:
    """Test per UserService — gestione utenti."""

    @pytest.fixture
    def service(self):
        """Fixture: istanza pulita per ogni test."""
        return UserService()

    def test_returns_user_when_id_exists(self, service):
        # Arrange
        user_id = "abc123"
        expected = {"id": user_id, "name": "Mario"}

        # Act
        with patch.object(service, "repository") as mock_repo:
            mock_repo.find_by_id.return_value = expected
            result = service.get_user(user_id)

        # Assert
        assert result["id"] == user_id
        assert result["name"] == "Mario"

    def test_raises_not_found_when_id_missing(self, service):
        # Arrange
        with patch.object(service, "repository") as mock_repo:
            mock_repo.find_by_id.return_value = None

        # Act & Assert
        with pytest.raises(UserNotFoundError):
            service.get_user("nonexistent")

    @pytest.mark.parametrize("invalid_id", ["", None, "   ", 123])
    def test_rejects_invalid_id_format(self, service, invalid_id):
        with pytest.raises(ValueError):
            service.get_user(invalid_id)
```

### Pattern TypeScript (Jest)

```typescript
// Categoria: unit
// File sorgente: src/services/userService.ts
// Creato: 2024-01-15

import { UserService } from '../../../src/services/userService';
import { UserRepository } from '../../../src/repositories/userRepository';

jest.mock('../../../src/repositories/userRepository');

describe('UserService', () => {
  let service: UserService;
  let mockRepo: jest.Mocked<UserRepository>;

  beforeEach(() => {
    mockRepo = new UserRepository() as jest.Mocked<UserRepository>;
    service = new UserService(mockRepo);
  });

  afterEach(() => jest.clearAllMocks());

  it('returns user when id exists', async () => {
    // Arrange
    const expected = { id: 'abc123', name: 'Mario' };
    mockRepo.findById.mockResolvedValue(expected);

    // Act
    const result = await service.getUser('abc123');

    // Assert
    expect(result).toEqual(expected);
  });

  it('throws NotFoundError when id is missing', async () => {
    // Arrange
    mockRepo.findById.mockResolvedValue(null);

    // Act & Assert
    await expect(service.getUser('ghost')).rejects.toThrow('NotFoundError');
  });

  it.each(['', null, undefined, 123])('rejects invalid id: %s', async (invalidId) => {
    await expect(service.getUser(invalidId as any)).rejects.toThrow('ValidationError');
  });
});
```

---

## INTEGRATION TEST

### Principi

- Usano un database/server **reale ma isolato** (es. DB di test, server in-process)
- Non mockano layer infrastrutturali — testano che i layer parlino correttamente tra loro
- Devono fare cleanup dopo ogni test (truncate tabelle, reset stato)

### Pattern Python (pytest + httpx)

```python
# Categoria: integration
# File sorgente: src/api/routes/users.py
# Creato: 2024-01-15

import pytest
import httpx
from src.main import create_app

@pytest.fixture(scope="module")
async def client():
    app = create_app(testing=True)
    async with httpx.AsyncClient(app=app, base_url="http://test") as c:
        yield c

@pytest.fixture(autouse=True)
async def clean_db(db_session):
    """Pulisce il DB dopo ogni test."""
    yield
    await db_session.execute("DELETE FROM users")
    await db_session.commit()

async def test_create_user_returns_201(client):
    # Arrange
    payload = {"name": "Mario", "email": "mario@example.com"}

    # Act
    response = await client.post("/api/users", json=payload)

    # Assert
    assert response.status_code == 201
    assert response.json()["email"] == "mario@example.com"

async def test_get_nonexistent_user_returns_404(client):
    response = await client.get("/api/users/nonexistent-id")
    assert response.status_code == 404
```

### Pattern TypeScript (Jest + Supertest)

```typescript
// Categoria: integration
// File sorgente: src/api/routes/users.ts
// Creato: 2024-01-15

import request from 'supertest';
import { createApp } from '../../../src/app';
import { db } from '../../../src/db';

const app = createApp({ testing: true });

afterEach(async () => {
  await db.raw('DELETE FROM users');
});

afterAll(async () => {
  await db.destroy();
});

describe('POST /api/users', () => {
  it('creates user and returns 201', async () => {
    const res = await request(app)
      .post('/api/users')
      .send({ name: 'Mario', email: 'mario@example.com' });

    expect(res.status).toBe(201);
    expect(res.body.email).toBe('mario@example.com');
  });
});
```

---

## E2E TEST — Playwright

### Principi

- Testano flussi utente completi dal browser
- Usano selettori robusti: preferire `data-testid` > ruolo > testo > CSS
- Mai sleep() fissi: usare `waitForSelector`, `waitForResponse`, `expect(locator).toBeVisible()`
- Ogni test deve essere indipendente (login se necessario, logout alla fine)

### Pattern Python

```python
# Categoria: e2e
# Flusso: login utente e accesso dashboard
# Creato: 2024-01-15

import pytest
from playwright.sync_api import Page, expect

BASE_URL = "http://localhost:8000"

@pytest.fixture(autouse=True)
def logout_after(page: Page):
    yield
    page.goto(f"{BASE_URL}/logout")

def test_user_can_login_and_see_dashboard(page: Page):
    # Arrange
    page.goto(f"{BASE_URL}/login")

    # Act
    page.get_by_label("Email").fill("mario@example.com")
    page.get_by_label("Password").fill("secret123")
    page.get_by_role("button", name="Accedi").click()

    # Assert
    expect(page).to_have_url(f"{BASE_URL}/dashboard")
    expect(page.get_by_test_id("welcome-message")).to_be_visible()
```

### Pattern TypeScript

```typescript
// Categoria: e2e
// Flusso: checkout prodotto
// Creato: 2024-01-15

import { test, expect } from '@playwright/test';

test.afterEach(async ({ page }) => {
  await page.goto('/logout');
});

test('user can add product to cart and checkout', async ({ page }) => {
  // Arrange
  await page.goto('/login');
  await page.getByLabel('Email').fill('mario@example.com');
  await page.getByRole('button', { name: 'Accedi' }).click();

  // Act
  await page.goto('/products');
  await page.getByTestId('product-123').getByRole('button', { name: 'Aggiungi' }).click();
  await page.getByRole('link', { name: 'Carrello' }).click();
  await page.getByRole('button', { name: 'Procedi al pagamento' }).click();

  // Assert
  await expect(page.getByTestId('order-confirmation')).toBeVisible();
});
```

---

## SECURITY — Cosa segnalare

L'agente non scrive test di sicurezza manualmente, esegue i tool (vedi toolstack.md)
e **interpreta i risultati**. Nel report deve:

1. Elencare ogni vulnerabilità trovata con: nome, severity, package/file, fix disponibile
2. Raggruppare per severity: CRITICAL → HIGH → MEDIUM → LOW
3. Per CRITICAL/HIGH: proporre immediatamente il comando di fix
4. Non ignorare mai una CRITICAL anche se il codice non la "usa direttamente"

---

## PERFORMANCE — Cosa misurare

1. **Tempo di risposta** delle API: confrontare con `performance.budget_ms` in qa.config.json
2. **Funzioni più lente** dal profiler: segnalare top-10 per tempo cumulativo
3. **Query SQL lente**: segnalare query con `EXPLAIN ANALYZE` > 100ms
4. **Memory leak**: segnalare se memoria cresce in modo anomalo durante il load test

---

## A11Y — Cosa verificare

Priorità degli errori axe-core / pa11y:

1. **critical/serious** → bloccare, devono essere risolti
2. **moderate** → segnalare, proporre fix
3. **minor** → loggare nel report

Categorie più comuni da controllare:
- Immagini senza `alt`
- Contrasto colore insufficiente (WCAG AA: 4.5:1 per testo normale)
- Form senza label associate
- Elementi interattivi non raggiungibili da tastiera
- Struttura heading non logica (h1 → h2 → h3, senza salti)