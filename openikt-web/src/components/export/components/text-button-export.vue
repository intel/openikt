<template>
  <div class="text-button-export-component">
    <el-button
      class="export-btn"
      type="text"
      icon="el-icon-download"
      :loading="isLoading || whetherLoading"
      @click="handleExport">
      Export
    </el-button>
  </div>
</template>

<script>
import { downloadExcelFile } from '@/utils'

export default {
  name: 'TextButtonExport',
  inject: {
    isLoading: {
      default: false
    }
  },
  props: {
    whetherLoading: {
      type: Boolean,
      default: false
    }
  },
  methods: {
    async handleExport() {
      const loading = this.$loading({
        lock: true,
        text: 'Downloading',
        spinner: 'el-icon-loading',
        background: 'rgba(0, 0, 0, 0.7)'
      })
      this.$emit('handle-export', (data, filename) => {
        downloadExcelFile(data, filename)
        loading.close()
      })
    }
  }
}
</script>

<style lang="scss" scoped>
.text-button-export-component {
  height: 32px;
  text-align: right;

  .export-btn {
    height: 100%;
    padding: 0;
    border: none;
    font-size: 18px;
  }
}
</style>
