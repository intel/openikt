<template>
  <div class="quilt-diff-component">
    <h2 class="title">Quilt Diff</h2>
    <quilt-diff-table></quilt-diff-table>
  </div>
</template>

<script>
import QuiltDiffTable from './components/QuiltDiffTable.vue'

export default {
  name: 'QuiltDiff',
  components: {
    QuiltDiffTable
  }
}
</script>

<style lang="scss" scoped>
.quilt-diff-component {
  padding: 10px 20px;

  .title {
    text-align: center;
  }
}
</style>
