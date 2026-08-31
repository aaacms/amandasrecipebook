import './styles.css'

const app = document.querySelector('#app')
const apiBaseUrl = (import.meta.env.VITE_API_URL ?? (import.meta.env.DEV ? '/api' : '')).replace(/\/$/, '')
const recipeId = /^\/recipe\/(\d+)\/?$/.exec(window.location.pathname)?.[1]

function categoryLabel(category) {
  return ({ breakfast: 'Café da manhã', meal: 'Refeição', snack: 'Lanche', dessert: 'Sobremesa', drink: 'Bebida', holiday: 'Data especial' })[category?.value] || 'Receita'
}

function recipeCard(savedRecipe) {
  const { recipe } = savedRecipe
  const card = document.createElement('a')
  card.href = `/recipe/${savedRecipe.id}`
  card.className = 'block rounded-2xl border border-stone-200 bg-white p-5 shadow-sm transition hover:-translate-y-0.5 hover:border-orange-300 hover:shadow-md focus:outline-none focus:ring-4 focus:ring-orange-100'
  const count = recipe.ingredients?.length || 0
  card.innerHTML = `<p class="text-sm font-semibold text-orange-600"></p><h3 class="mt-1 text-lg font-bold leading-snug text-stone-900"></h3><p class="mt-3 text-sm text-stone-600"></p><p class="mt-4 text-sm font-semibold text-orange-600">Ver receita →</p>`
  card.querySelectorAll('p')[0].textContent = categoryLabel(recipe.category)
  card.querySelector('h3').textContent = recipe.title
  card.querySelectorAll('p')[1].textContent = `${count} ingrediente${count === 1 ? '' : 's'}${recipe.source?.author ? ` · ${recipe.source.author}` : ''}`
  return card
}

function renderHome() {
  app.innerHTML = `
    <main class="mx-auto flex min-h-screen w-full max-w-5xl flex-col px-5 py-8 sm:px-8 sm:py-12">
      <header class="mb-12 flex items-center gap-3"><div class="grid size-11 place-items-center rounded-2xl bg-orange-500 text-xl shadow-sm" aria-hidden="true">🍲</div><div><p class="text-sm font-medium text-orange-600">Seu caderno digital</p><h1 class="text-xl font-bold tracking-tight sm:text-2xl">Livro de Receitas</h1></div></header>
      <section class="mx-auto w-full max-w-2xl" aria-labelledby="import-title"><div class="rounded-3xl border border-stone-200 bg-white p-6 shadow-sm sm:p-8"><p class="mb-2 text-sm font-semibold text-orange-600">Nova receita</p><h2 id="import-title" class="text-2xl font-bold tracking-tight sm:text-3xl">Importe uma receita da web</h2><p class="mt-3 text-stone-600">Cole o link de uma receita para salvá-la no seu livro.</p><form id="recipe-import-form" class="mt-7 flex flex-col gap-3 sm:flex-row" novalidate><label class="sr-only" for="recipe-url">URL da receita</label><input id="recipe-url" name="recipeUrl" type="url" inputmode="url" placeholder="https://exemplo.com/minha-receita" required class="min-w-0 flex-1 rounded-xl border border-stone-300 bg-white px-4 py-3 text-base outline-none transition placeholder:text-stone-400 focus:border-orange-500 focus:ring-4 focus:ring-orange-100" /><button type="submit" class="rounded-xl bg-orange-500 px-5 py-3 font-semibold text-white transition hover:bg-orange-600 focus:outline-none focus:ring-4 focus:ring-orange-200 active:bg-orange-700 disabled:cursor-wait disabled:opacity-70">Importar receita</button></form><p id="form-message" class="mt-3 hidden text-sm" role="status"></p></div></section>
      <section class="mx-auto mt-12 w-full max-w-2xl" aria-labelledby="saved-recipes-title"><div class="mb-5 flex items-end justify-between gap-4"><div><p class="text-sm font-semibold text-orange-600">Seu livro</p><h2 id="saved-recipes-title" class="text-2xl font-bold tracking-tight">Receitas salvas</h2></div><span id="recipes-count" class="text-sm text-stone-500"></span></div><p id="recipes-status" class="text-sm text-stone-600" role="status">Carregando receitas...</p><div id="recipes-list" class="mt-4 grid gap-3 sm:grid-cols-2"></div></section>
    </main>`

  const form = document.querySelector('#recipe-import-form')
  const urlInput = document.querySelector('#recipe-url')
  const message = document.querySelector('#form-message')
  const submitButton = form.querySelector('button[type="submit"]')
  const recipesList = document.querySelector('#recipes-list')
  const recipesStatus = document.querySelector('#recipes-status')
  const recipesCount = document.querySelector('#recipes-count')

  async function loadRecipes() {
    try {
      const response = await fetch(`${apiBaseUrl}/recipes`)
      if (!response.ok) throw new Error()
      const recipes = await response.json()
      recipesList.replaceChildren(...recipes.map(recipeCard))
      recipesCount.textContent = `${recipes.length} receita${recipes.length === 1 ? '' : 's'}`
      recipesStatus.classList.toggle('hidden', recipes.length > 0)
      recipesStatus.textContent = recipes.length ? '' : 'Nenhuma receita salva ainda.'
    } catch {
      recipesStatus.textContent = 'Não foi possível carregar as receitas salvas.'
      recipesStatus.className = 'text-sm text-red-600'
    }
  }

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
      const response = await fetch(`${apiBaseUrl}/recipes`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ url: urlInput.value.trim() }) })
      const data = await response.json().catch(() => ({}))
      if (!response.ok) throw new Error(data.detail || 'Não foi possível importar esta receita.')
      message.textContent = `Receita “${data.recipe.title}” importada com sucesso!`
      message.className = 'mt-3 text-sm text-emerald-700'
      urlInput.value = ''
      await loadRecipes()
    } catch (error) {
      message.textContent = error.message || 'Não foi possível conectar à API.'
      message.className = 'mt-3 text-sm text-red-600'
    } finally {
      submitButton.disabled = false
      submitButton.textContent = 'Importar receita'
    }
  })
  loadRecipes()
}

function textList(element, values, emptyText, numbered = false) {
  if (!values?.length) {
    element.textContent = emptyText
    return
  }
  values.forEach((value) => {
    const item = document.createElement('li')
    item.textContent = typeof value === 'string' ? value : [value.quantity, value.unit, value.name].filter(Boolean).join(' ')
    element.append(item)
  })
  if (numbered) element.className += ' list-decimal pl-5'
}

function renderRecipeDetail(savedRecipe) {
  const { recipe } = savedRecipe
  app.innerHTML = `<main class="mx-auto min-h-screen w-full max-w-3xl px-5 py-8 sm:px-8 sm:py-12"><a href="/" class="inline-flex text-sm font-semibold text-orange-600 hover:text-orange-700">← Voltar ao livro</a><article class="mt-8 rounded-3xl border border-stone-200 bg-white p-6 shadow-sm sm:p-10"><p id="category" class="text-sm font-semibold text-orange-600"></p><h1 class="mt-2 text-3xl font-bold tracking-tight text-stone-900 sm:text-4xl"></h1><div id="facts" class="mt-6 flex flex-wrap gap-3"></div><section class="mt-10"><h2 class="text-xl font-bold">Ingredientes</h2><ul id="ingredients" class="mt-4 space-y-2 text-stone-700"></ul></section><section class="mt-10"><h2 class="text-xl font-bold">Modo de preparo</h2><ol id="instructions" class="mt-4 space-y-3 text-stone-700"></ol></section><section class="mt-10 border-t border-stone-200 pt-6"><h2 class="text-lg font-bold">Origem</h2><p id="source" class="mt-2 text-sm text-stone-600"></p></section></article></main>`
  document.querySelector('#category').textContent = categoryLabel(recipe.category)
  document.querySelector('h1').textContent = recipe.title
  const minutes = (metric) => metric?.value === null || metric?.value === undefined ? null : `${metric.value} min`
  const facts = [['Porções', recipe.servings?.value], ['Preparo', minutes(recipe.prep_time_minutes)], ['Cozimento', minutes(recipe.cook_time_minutes)]]
  facts.filter(([, value]) => value !== null && value !== undefined).forEach(([label, value]) => {
    const item = document.createElement('span')
    item.className = 'rounded-full bg-orange-50 px-3 py-1 text-sm text-orange-800'
    item.textContent = `${label}: ${value}`
    document.querySelector('#facts').append(item)
  })
  textList(document.querySelector('#ingredients'), recipe.ingredients, 'Ingredientes não informados.')
  textList(document.querySelector('#instructions'), recipe.instructions, 'Modo de preparo não informado.', true)
  const source = document.querySelector('#source')
  source.textContent = [recipe.source?.author, recipe.source?.platform].filter(Boolean).join(' · ')
  if (recipe.source?.url) {
    const link = document.createElement('a')
    link.href = recipe.source.url
    link.target = '_blank'
    link.rel = 'noreferrer'
    link.className = 'ml-2 font-semibold text-orange-600 hover:text-orange-700'
    link.textContent = 'Ver publicação original ↗'
    source.append(link)
  }
}

async function loadRecipeDetail(id) {
  app.innerHTML = '<main class="mx-auto min-h-screen w-full max-w-3xl px-5 py-12 text-stone-600">Carregando receita...</main>'
  try {
    const response = await fetch(`${apiBaseUrl}/recipes/${id}`)
    if (response.status === 404) throw new Error('Receita não encontrada.')
    if (!response.ok) throw new Error('Não foi possível carregar a receita.')
    renderRecipeDetail(await response.json())
  } catch (error) {
    app.innerHTML = '<main class="mx-auto min-h-screen w-full max-w-3xl px-5 py-12"><a href="/" class="font-semibold text-orange-600">← Voltar ao livro</a><p class="mt-6 text-red-600"></p></main>'
    document.querySelector('main p').textContent = error.message
  }
}

if (recipeId) loadRecipeDetail(recipeId)
else renderHome()
