import './styles.css'

const app = document.querySelector('#app')

app.innerHTML = `
  <main class="mx-auto flex min-h-screen w-full max-w-5xl flex-col px-5 py-8 sm:px-8 sm:py-12">
    <header class="mb-12 flex items-center gap-3">
      <div class="grid size-11 place-items-center rounded-2xl bg-orange-500 text-xl shadow-sm" aria-hidden="true">🍲</div>
      <div>
        <p class="text-sm font-medium text-orange-600">Seu caderno digital</p>
        <h1 class="text-xl font-bold tracking-tight sm:text-2xl">Livro de Receitas</h1>
      </div>
    </header>

    <section class="mx-auto w-full max-w-2xl" aria-labelledby="import-title">
      <div class="rounded-3xl border border-stone-200 bg-white p-6 shadow-sm sm:p-8">
        <p class="mb-2 text-sm font-semibold text-orange-600">Nova receita</p>
        <h2 id="import-title" class="text-2xl font-bold tracking-tight sm:text-3xl">Importe uma receita da web</h2>
        <p class="mt-3 text-stone-600">Cole o link de uma receita para salvá-la no seu livro.</p>
        <form id="recipe-import-form" class="mt-7 flex flex-col gap-3 sm:flex-row" novalidate>
          <label class="sr-only" for="recipe-url">URL da receita</label>
          <input id="recipe-url" name="recipeUrl" type="url" inputmode="url" placeholder="https://exemplo.com/minha-receita" required class="min-w-0 flex-1 rounded-xl border border-stone-300 bg-white px-4 py-3 text-base outline-none transition placeholder:text-stone-400 focus:border-orange-500 focus:ring-4 focus:ring-orange-100" />
          <button type="submit" class="rounded-xl bg-orange-500 px-5 py-3 font-semibold text-white transition hover:bg-orange-600 focus:outline-none focus:ring-4 focus:ring-orange-200 active:bg-orange-700 disabled:cursor-wait disabled:opacity-70">Importar receita</button>
        </form>
        <p id="form-message" class="mt-3 hidden text-sm" role="status"></p>
      </div>
    </section>
  </main>
`

const form = document.querySelector('#recipe-import-form')
const urlInput = document.querySelector('#recipe-url')
const message = document.querySelector('#form-message')
const submitButton = form.querySelector('button[type="submit"]')
const apiBaseUrl = (
  import.meta.env.VITE_API_URL ?? (import.meta.env.DEV ? '/api' : '')
).replace(/\/$/, '')

form.addEventListener('submit', async (event) => {
  event.preventDefault()

  if (!urlInput.checkValidity()) {
    message.textContent = 'Informe uma URL válida para importar a receita.'
    message.className = 'mt-3 text-sm text-red-600'
    urlInput.focus()
    return
  }

  submitButton.disabled = true
  submitButton.textContent = 'Importando...'
  message.textContent = 'Estamos extraindo a receita. Isso pode levar alguns instantes.'
  message.className = 'mt-3 text-sm text-stone-600'

  try {
    const response = await fetch(`${apiBaseUrl}/recipes`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ url: urlInput.value.trim() }),
    })
    const data = await response.json().catch(() => ({}))

    if (!response.ok) {
      throw new Error(data.detail || 'Não foi possível importar esta receita.')
    }

    message.textContent = `Receita “${data.recipe.title}” importada com sucesso!`
    message.className = 'mt-3 text-sm text-emerald-700'
    urlInput.value = ''
  } catch (error) {
    message.textContent = error.message || 'Não foi possível conectar à API.'
    message.className = 'mt-3 text-sm text-red-600'
  } finally {
    submitButton.disabled = false
    submitButton.textContent = 'Importar receita'
  }
})
