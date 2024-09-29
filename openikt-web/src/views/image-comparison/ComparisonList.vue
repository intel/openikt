<template>
  <div class="image-comparison-list-component">
    <h2 class="title">Image Comparison</h2>

    <el-row style="margin-bottom: 20px">
      <el-col :span="6">
        <el-select
          v-model="imageComparisonId"
          placeholder="Image Comparison"
          size="small"
          style="width: 100%"
          clearable
          @change="changeImageComparisonSelector">
          <el-option
            v-for="item of imageComparisonOptions"
            :key="item.value"
            :label="item.label"
            :value="item.value"></el-option>
        </el-select>
      </el-col>

      <el-col :span="18" style="text-align: right">
        <el-button type="success" size="small" @click="toCreatePage">
          Create
        </el-button>
      </el-col>
    </el-row>

    <el-table
      class="ikt-table"
      :data="tableData"
      v-loading="isLoadingTableData"
      size="small"
      border>
      <el-table-column
        type="index"
        fixed
        align="center"
        width="50"></el-table-column>

      <el-table-column
        prop="img_a"
        label="Image"
        min-width="200"
        show-overflow-tooltip>
        <template #default="{ row }">
          <div
            style="cursor: pointer"
            @click="toDetailsPage(row.id, row.img_a, row.img_b)">
            <div>{{ row.img_a }}</div>
            <div>{{ row.img_b }}</div>
          </div>
        </template>
      </el-table-column>

      <el-table-column
        prop="release_a"
        label="Release"
        min-width="150"
        show-overflow-tooltip>
        <template #default="{ row }">
          <div>{{ row.release_a }}</div>
          <div>{{ row.release_b }}</div>
        </template>
      </el-table-column>

      <el-table-column prop="urlA" label="URL" min-width="300">
        <template #default="{ row }">
          <div>
            <el-link :underline="false" :href="row.urlA" target="_blank">
              {{ row.urlA }}
            </el-link>
          </div>
          <div>
            <el-link :underline="false" :href="row.urlB" target="_blank">
              {{ row.urlB }}
            </el-link>
          </div>
        </template>
      </el-table-column>

      <el-table-column
        prop="created"
        label="Created Date"
        header-align="center"
        align="center"
        width="180"
        show-overflow-tooltip></el-table-column>
    </el-table>
  </div>
</template>

<script>
import Cookies from 'js-cookie'
import {
  getImageComparisonListAPI,
  getImageComparisonTableDataAPI
} from '@/services/api/image-comparison'

export default {
  name: 'ImageComparisonList',
  data() {
    return {
      isLoadingTableData: false,
      tableData: [],
      imageComparisonOptions: [],
      imageComparisonId: ''
    }
  },
  methods: {
    parsingQuery() {
      const id = this.$route.query.id
      id && (this.imageComparisonId = id)
      this.getTableData(id)
    },
    toDetailsPage(imageComparisonId, imgA, imgB) {
      window.open(
        `/openikt/image-comparison/details/${imageComparisonId}?imgA=${imgA}&imgB=${imgB}`,
        '_blank'
      )
    },
    toCreatePage() {
      if (!Cookies.get('username')) {
        this.$router.push('/welcome')
        return
      }

      window.open('/openikt/image-comparison/create', '_blank')
    },
    changeImageComparisonSelector(id) {
      if (id) {
        this.$router.replace({
          query: {
            id
          }
        })
      } else {
        this.$router.replace({
          query: {}
        })
      }

      this.getTableData(id)
    },
    async getImageComparisonSelectorOptions() {
      ;({ data: this.imageComparisonOptions } =
        await getImageComparisonListAPI())
    },
    async getTableData(imageComparisonId) {
      this.isLoadingTableData = true
      const { data } = await getImageComparisonTableDataAPI(imageComparisonId)
      this.tableData = data.tableData
      this.isLoadingTableData = false
    }
  },
  created() {
    this.getImageComparisonSelectorOptions()
    this.parsingQuery()
  }
}
</script>

<style lang="scss" scoped>
.image-comparison-list-component {
  padding: 10px 20px;

  .title {
    text-align: center;
  }

  .el-link {
    font-size: 12px;

    &:link {
      color: #409eff;
    }

    &:hover {
      color: #06b6d4;
    }
  }
}
</style>
