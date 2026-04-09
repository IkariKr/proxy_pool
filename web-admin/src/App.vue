<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'

const apiBase = window.location.port === '5173' ? '/api' : ''

const dashboard = ref({
  count: 0,
  candidate_count: 0,
  qualified_count: 0,
  http_type: {},
  source: {}
})
const proxies = ref([])
const drawnProxy = ref(null)
const loading = ref(false)
const errorMessage = ref('')
const actionMessage = ref('')
const scope = ref('qualified')
const protocol = ref('all')
const search = ref('')
const autoRefresh = ref(true)
const lastUpdated = ref('')
let refreshTimer = null

const statCards = computed(() => [
  { label: '主池代理', value: dashboard.value.qualified_count ?? 0, tone: 'primary' },
  { label: '候选代理', value: dashboard.value.candidate_count ?? 0, tone: 'secondary' },
  { label: 'HTTP 主池', value: dashboard.value.http_type?.http ?? 0, tone: 'neutral' },
  { label: 'HTTPS 主池', value: dashboard.value.http_type?.https ?? 0, tone: 'accent' },
  { label: 'SOCKS5 主池', value: dashboard.value.http_type?.socks5 ?? 0, tone: 'socks' }
])

const sourceRows = computed(() =>
  Object.entries(dashboard.value.source || {})
    .map(([name, count]) => ({ name, count }))
    .sort((a, b) => b.count - a.count)
)

const filteredProxies = computed(() => {
  const keyword = search.value.trim().toLowerCase()
  return proxies.value.filter((proxy) => {
    const currentProtocol = proxy.proxy_type === 'socks5' ? 'socks5' : (proxy.https ? 'https' : 'http')
    const protocolMatch = protocol.value === 'all' || protocol.value === currentProtocol

    if (!protocolMatch) {
      return false
    }

    if (!keyword) {
      return true
    }

    return [
      proxy.proxy,
      proxy.exit_ip,
      proxy.source,
      proxy.region,
      proxy.proxy_type
    ]
      .filter(Boolean)
      .some((value) => String(value).toLowerCase().includes(keyword))
  })
})

function toExportLine(proxyValue) {
  const raw = String(proxyValue || '').trim()
  if (!raw) {
    return ''
  }

  let credentialPart = ''
  let hostPart = raw

  if (raw.includes('@')) {
    const pieces = raw.split('@')
    credentialPart = pieces[0] || ''
    hostPart = pieces[1] || ''
  }

  const hostPieces = hostPart.split(':')
  const host = hostPieces[0] || ''
  const port = hostPieces.slice(1).join(':') || ''

  let user = ''
  let pass = ''
  if (credentialPart) {
    const credentialPieces = credentialPart.split(':')
    user = credentialPieces[0] || ''
    pass = credentialPieces.slice(1).join(':') || ''
  }

  if (!user && !pass) {
    return [host, port].join(':')
  }

  return [host, port, user, pass].join(':')
}

const exportLines = computed(() =>
  filteredProxies.value
    .map((proxy) => toExportLine(proxy.proxy))
    .filter(Boolean)
)

function apiUrl(path) {
  return `${apiBase}${path}`
}

async function requestJson(path, options = {}) {
  const response = await fetch(apiUrl(path), options)
  if (!response.ok) {
    throw new Error(`请求失败: ${response.status}`)
  }
  return response.json()
}

async function loadDashboard() {
  dashboard.value = await requestJson('/count/')
}

async function loadProxyList() {
  const params = new URLSearchParams()
  if (scope.value === 'all') {
    params.set('scope', 'all')
  }
  if (protocol.value === 'https' || protocol.value === 'socks5') {
    params.set('type', protocol.value)
  }
  const query = params.toString()
  proxies.value = await requestJson(`/all/${query ? `?${query}` : ''}`)
}

async function refreshAll() {
  loading.value = true
  errorMessage.value = ''
  try {
    await Promise.all([loadDashboard(), loadProxyList()])
    lastUpdated.value = new Date().toLocaleString('zh-CN', { hour12: false })
  } catch (error) {
    errorMessage.value = error.message || '刷新失败'
  } finally {
    loading.value = false
  }
}

async function drawProxy(mode) {
  actionMessage.value = ''
  errorMessage.value = ''
  try {
    const params = new URLSearchParams()
    if (protocol.value === 'https' || protocol.value === 'socks5') {
      params.set('type', protocol.value)
    }
    const query = params.toString()
    const data = await requestJson(`/${mode}/${query ? `?${query}` : ''}`)
    if (data.code === 0) {
      actionMessage.value = '当前没有可用主池代理'
      drawnProxy.value = null
      return
    }
    drawnProxy.value = data
    actionMessage.value = mode === 'get' ? '已抽取一个代理' : '已弹出一个代理'
    await refreshAll()
  } catch (error) {
    errorMessage.value = error.message || '抽取失败'
  }
}

async function deleteProxy(proxy) {
  actionMessage.value = ''
  errorMessage.value = ''
  try {
    const params = new URLSearchParams({ proxy })
    await requestJson(`/delete/?${params.toString()}`)
    actionMessage.value = `已删除 ${proxy}`
    if (drawnProxy.value?.proxy === proxy) {
      drawnProxy.value = null
    }
    await refreshAll()
  } catch (error) {
    errorMessage.value = error.message || '删除失败'
  }
}

async function copyText(text) {
  try {
    await navigator.clipboard.writeText(text)
    actionMessage.value = `已复制 ${text}`
  } catch (error) {
    errorMessage.value = '复制失败，请检查浏览器权限'
  }
}

async function copyExport() {
  if (!exportLines.value.length) {
    actionMessage.value = '当前没有可导出的代理'
    return
  }
  await copyText(exportLines.value.join('\n'))
  actionMessage.value = `已复制 ${exportLines.value.length} 条导出代理`
}

function downloadExport() {
  if (!exportLines.value.length) {
    actionMessage.value = '当前没有可导出的代理'
    return
  }

  const content = exportLines.value.join('\n')
  const blob = new Blob([content], { type: 'text/plain;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  const stamp = new Date().toISOString().replace(/[:.]/g, '-')
  link.href = url
  link.download = `proxy-export-${scope.value}-${protocol.value}-${stamp}.txt`
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
  actionMessage.value = `已导出 ${exportLines.value.length} 条代理`
}

function resetAutoRefresh() {
  if (refreshTimer) {
    clearInterval(refreshTimer)
    refreshTimer = null
  }

  if (autoRefresh.value) {
    refreshTimer = setInterval(() => {
      refreshAll()
    }, 15000)
  }
}

onMounted(async () => {
  await refreshAll()
  resetAutoRefresh()
})

onBeforeUnmount(() => {
  if (refreshTimer) {
    clearInterval(refreshTimer)
  }
})
</script>

<template>
  <div class="shell">
    <aside class="hero-panel">
      <div class="hero-copy">
        <p class="eyebrow">Proxy Pool Admin</p>
        <h1>代理池后台总览</h1>
        <p class="hero-text">
          用一个页面看主池、候选池、来源分布和代理详情，顺手完成抽取、复制、导出和删除这些日常动作。
        </p>
      </div>

      <div class="draw-card">
        <div class="draw-header">
          <div>
            <p class="panel-label">快速抽取</p>
            <h2>主池代理</h2>
          </div>
          <span class="status-chip" :class="{ live: autoRefresh }">
            {{ autoRefresh ? '自动刷新中' : '手动模式' }}
          </span>
        </div>

        <div class="draw-actions">
          <button class="primary-btn" @click="drawProxy('get')">抽一个</button>
          <button class="ghost-btn" @click="drawProxy('pop')">抽并移除</button>
        </div>

        <div v-if="drawnProxy" class="draw-result">
          <div class="draw-proxy">{{ drawnProxy.proxy }}</div>
          <div class="draw-meta">
            <span>{{ drawnProxy.proxy_type === 'socks5' ? 'SOCKS5' : (drawnProxy.https ? 'HTTPS' : 'HTTP') }}</span>
            <span>得分 {{ drawnProxy.score ?? 0 }}</span>
            <span>出口 {{ drawnProxy.exit_ip || '未知' }}</span>
          </div>
          <div class="draw-actions">
            <button class="secondary-btn" @click="copyText(drawnProxy.proxy)">复制代理</button>
            <button class="danger-btn" @click="deleteProxy(drawnProxy.proxy)">删除</button>
          </div>
        </div>
        <div v-else class="empty-draw">
          当前还没有已抽取的代理，点击上方按钮就可以直接拿一个主池代理。
        </div>
      </div>
    </aside>

    <main class="main-panel">
      <section class="toolbar">
        <div class="toolbar-left">
          <div class="select-group">
            <button class="filter-btn" :class="{ active: scope === 'qualified' }" @click="scope = 'qualified'; refreshAll()">
              主池
            </button>
            <button class="filter-btn" :class="{ active: scope === 'all' }" @click="scope = 'all'; refreshAll()">
              全部候选
            </button>
          </div>

          <div class="select-group">
            <button class="filter-btn" :class="{ active: protocol === 'all' }" @click="protocol = 'all'; refreshAll()">
              全协议
            </button>
            <button class="filter-btn" :class="{ active: protocol === 'http' }" @click="protocol = 'http'; refreshAll()">
              HTTP
            </button>
            <button class="filter-btn" :class="{ active: protocol === 'https' }" @click="protocol = 'https'; refreshAll()">
              HTTPS
            </button>
            <button class="filter-btn" :class="{ active: protocol === 'socks5' }" @click="protocol = 'socks5'; refreshAll()">
              SOCKS5
            </button>
          </div>
        </div>

        <div class="toolbar-right">
          <label class="toggle">
            <input v-model="autoRefresh" type="checkbox" @change="resetAutoRefresh" />
            <span>自动刷新</span>
          </label>
          <input v-model="search" class="search-input" type="text" placeholder="搜索代理、出口 IP、来源" />
          <button class="ghost-btn" @click="copyExport">复制导出</button>
          <button class="ghost-btn" @click="downloadExport">导出 TXT</button>
          <button class="secondary-btn" :disabled="loading" @click="refreshAll">
            {{ loading ? '刷新中...' : '立即刷新' }}
          </button>
        </div>
      </section>

      <section class="stats-grid">
        <article v-for="card in statCards" :key="card.label" class="stat-card" :data-tone="card.tone">
          <p>{{ card.label }}</p>
          <strong>{{ card.value }}</strong>
        </article>
      </section>

      <section class="message-row">
        <p v-if="lastUpdated" class="hint-text">最近刷新：{{ lastUpdated }}</p>
        <p v-if="actionMessage" class="success-text">{{ actionMessage }}</p>
        <p v-if="errorMessage" class="error-text">{{ errorMessage }}</p>
      </section>

      <section class="content-grid">
        <article class="panel">
          <div class="panel-head">
            <div>
              <p class="panel-label">来源分布</p>
              <h2>主池来源统计</h2>
            </div>
          </div>

          <div v-if="sourceRows.length" class="source-list">
            <div v-for="row in sourceRows" :key="row.name" class="source-row">
              <span>{{ row.name }}</span>
              <strong>{{ row.count }}</strong>
            </div>
          </div>
          <div v-else class="empty-state">当前主池还没有来源统计。</div>
        </article>

        <article class="panel table-panel">
          <div class="panel-head">
            <div>
              <p class="panel-label">代理列表</p>
              <h2>{{ scope === 'qualified' ? '主池代理' : '候选与主池' }}</h2>
            </div>
            <span class="table-count">{{ filteredProxies.length }} 条</span>
          </div>

          <div class="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>代理</th>
                  <th>协议</th>
                  <th>得分</th>
                  <th>连续通过</th>
                  <th>出口 IP</th>
                  <th>来源</th>
                  <th>状态</th>
                  <th>操作</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="proxy in filteredProxies" :key="`${proxy.proxy_type || 'http'}-${proxy.proxy}`">
                  <td class="proxy-cell">
                    <strong>{{ proxy.proxy }}</strong>
                    <small>{{ proxy.region || '未知地区' }}</small>
                  </td>
                  <td>{{ proxy.proxy_type === 'socks5' ? 'SOCKS5' : (proxy.https ? 'HTTPS' : 'HTTP') }}</td>
                  <td>{{ proxy.score ?? 0 }}</td>
                  <td>{{ proxy.success_streak ?? 0 }}</td>
                  <td>{{ proxy.exit_ip || '未识别' }}</td>
                  <td class="source-cell">{{ proxy.source || '未知来源' }}</td>
                  <td>
                    <span class="pill" :class="proxy.qualified ? 'pill-ok' : 'pill-warm'">
                      {{ proxy.qualified ? '主池' : '候选' }}
                    </span>
                  </td>
                  <td class="action-cell">
                    <button class="link-btn" @click="copyText(proxy.proxy)">复制</button>
                    <button class="link-btn danger-link" @click="deleteProxy(proxy.proxy)">删除</button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </article>
      </section>
    </main>
  </div>
</template>
