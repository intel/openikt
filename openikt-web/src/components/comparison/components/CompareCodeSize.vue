<template>
  <div class="compare-code-size-component">
    <div class="size-delete-container">
      <div
        class="size-delete"
        :title="'-' + codeSize.deleteSize"
        :style="{ width: deleteWidth }"></div>
    </div>

    <div class="size-add-container">
      <div
        class="size-add"
        :title="'+' + codeSize.addSize"
        :style="{ width: addWidth }"></div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'CompareCodeSize',
  props: {
    codeSize: {
      type: Object,
      default: () => ({ addSize: 0, deleteSize: 0 })
    }
  },
  computed: {
    sumCodeSize() {
      return this.codeSize.addSize + this.codeSize.deleteSize
    },
    addWidth() {
      return (this.codeSize.addSize / this.sumCodeSize) * 100 + '%'
    },
    deleteWidth() {
      return (this.codeSize.deleteSize / this.sumCodeSize) * 100 + '%'
    }
  }
}
</script>

<style lang="scss" scoped>
.compare-code-size-component {
  display: flex;

  .size-delete-container {
    flex: 1;
    display: flex;
    justify-content: flex-end;

    .size-delete {
      height: 5px;
      background-color: #f43f5e;
    }
  }

  .size-add-container {
    flex: 1;
    display: flex;
    justify-content: flex-start;

    .size-add {
      height: 5px;
      background-color: #22c55e;
    }
  }
}
</style>
