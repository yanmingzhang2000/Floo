Page({
  data: {
    url: 'https://yanmingzhang2000.github.io/Floo/',
    loading: true,
    error: false
  },

  onLoad() {
    console.log('Loading Floo! web app...')
  },

  onWebViewLoad(e) {
    this.setData({ loading: false })
    console.log('Web view loaded successfully')
  },

  onWebViewError(e) {
    console.error('Web view error:', e.detail)
    this.setData({ error: true, loading: false })
  },

  onRetry() {
    this.setData({ loading: true, error: false })
    // Reload by changing url slightly then back
    this.setData({ url: '' })
    setTimeout(() => {
      this.setData({ url: 'https://yanmingzhang2000.github.io/Floo/' })
    }, 100)
  }
})
