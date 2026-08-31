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
          <input
            id="recipe-url"
            name="recipeUrl"
            type="url"
            inputmode="url"
            placeholder="https://exemplo.com/minha-receita"
            required
            class="min-w-0 flex-1 rounded-xl border border-stone-300 bg-white px-4 py-3 text-base outline-none transition placeholder:text-stone-400 focus:border-orange-500 focus:ring-4 focus:ring-orange-100"
          />
          <button type="submit" class="rounded-xl bg-orange-500 px-5 py-3 font-semibold text-white transition hover:bg-orange-600 focus:outline-none focus:ring-4 focus:ring-orange-200 active:bg-orange-700">
            Importar receita
          </button>
        </form>
        <p id="form-message" class="mt-3 hidden text-sm" role="status"></p>
      </div>
    </section>

    <section class="mx-auto mt-14 w-full max-w-2xl" aria-labelledby="saved-recipes-title">
      <div class="flex items-center justify-between gap-4">
        <div>
          <p class="text-sm font-semibold text-orange-600">Sua coleção</p>
          <h2 id="saved-recipes-title" class="text-2xl font-bold tracking-tight">Receitas salvas</h2>
        </div>
        <span class="rounded-full bg-stone-200 px-3 py-1 text-sm font-medium text-stone-600">Em breve</span>
      </div>
      <div class="mt-5 rounded-3xl border border-dashed border-stone-300 bg-white/60 px-6 py-12 text-center">
        <p class="text-lg font-semibold">Sua coleção aparecerá aqui.</p>
        <p class="mt-2 text-sm text-stone-600">Importe sua primeira receita usando o campo acima.</p>
      </div>
    </section>
  </main>
`

const form = document.querySelector('#recipe-import-form')
const urlInput = document.querySelector('#recipe-url')
const message = document.querySelector('#form-message')

form.addEventListener('submit', (event) => {
  event.preventDefault()

  if (!urlInput.checkValidity()) {
    message.textContent = 'Informe uma URL válida para importar a receita.'
    message.className = 'mt-3 text-sm text-red-600'
    urlInput.focus()
    return
  }

  // Futuramente, envie esta URL para a API FastAPI responsável pela importação.
  message.textContent = 'A importação será conectada à API em breve.'
  message.className = 'mt-3 text-sm text-emerald-700'
})
