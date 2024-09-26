<template>
  <div class="image-comparison-details-component">
    <h2 class="title">Image Comparison Details</h2>

    <h3>
      {{ imgA }}
      <i
        class="iconfont icon-bijiao"
        style="font-size: 22px; color: #ff5959"></i>
      {{ imgB }}
    </h3>

    <el-row :gutter="20" style="margin-bottom: 20px">
      <el-col :span="6">
        <el-select
          v-model="comparisonType"
          placeholder="Comparison Type"
          size="small"
          style="width: 100%"
          multiple
          collapse-tags
          clearable>
          <el-option
            v-for="item of comparisonTypeOptions"
            :key="item.value"
            :label="item.label"
            :value="item.value"></el-option>
        </el-select>
      </el-col>

      <el-col :span="6">
        <el-input
          v-model="packageName"
          placeholder="Package Name"
          size="small"
          clearable></el-input>
      </el-col>

      <el-col :span="4">
        <el-button type="primary" size="small" @click="getTableData">
          Search
        </el-button>
      </el-col>
    </el-row>

    <el-table
      class="ikt-table details-table"
      :data="tableData"
      v-loading="isLoadingTableData"
      size="small"
      border
      @expand-change="expandRowChange">
      <el-table-column type="expand">
        <template #default="{ row }">
          <div class="expand-details-container">
            <el-card
              v-if="row.detilsA"
              shadow="always"
              :body-style="{ padding: '20px' }">
              <el-descriptions
                class="desc-a"
                :title="`PKG A: ${row.pkg_a?.name}`"
                :column="3"
                size="mini"
                key="desc1"
                border
                :labelStyle="{ color: '#64748b', fontWeight: '700' }"
                :contentStyle="{ color: '#334155', fontWeight: '700' }">
                <el-descriptions-item label="Name">
                  {{ row.detilsA.name }}
                </el-descriptions-item>

                <el-descriptions-item label="Version">
                  {{ row.detilsA.version }}
                </el-descriptions-item>

                <el-descriptions-item label="Summary">
                  {{ row.detilsA.summary }}
                </el-descriptions-item>

                <el-descriptions-item label="Descriptions" :span="3">
                  {{ row.detilsA.desc }}
                </el-descriptions-item>

                <el-descriptions-item label="Home Page" :span="3">
                  <el-link
                    v-if="row.detilsA.homepage"
                    :underline="false"
                    :href="row.detilsA.homepage"
                    target="_blank">
                    {{ row.detilsA.homepage }}
                  </el-link>
                </el-descriptions-item>

                <el-descriptions-item label="Image">
                  {{ row.detilsA.img_name }}
                </el-descriptions-item>

                <el-descriptions-item label="Source">
                  {{ row.detilsA.source }}
                </el-descriptions-item>

                <el-descriptions-item label="Arch">
                  {{ row.detilsA.arch }}
                </el-descriptions-item>

                <el-descriptions-item label="Section Name" :span="3">
                  <div>{{ row.detilsA.section_info.name }}</div>
                </el-descriptions-item>

                <el-descriptions-item label="Relation" :span="3">
                  <div
                    v-for="(item, index) of row.detilsA.relation"
                    :key="index">
                    {{ item }}
                  </div>
                </el-descriptions-item>

                <el-descriptions-item label="Contributor" :span="3">
                  <div
                    v-for="(item, index) of row.detilsA.contributor"
                    :key="index">
                    {{ item }}
                  </div>
                </el-descriptions-item>
              </el-descriptions>
            </el-card>

            <el-card
              v-if="row.detilsB"
              shadow="always"
              :body-style="{ padding: '20px' }"
              :style="{
                marginLeft: row.detilsA && row.detilsB ? '20px' : '0'
              }">
              <el-descriptions
                class="desc-b"
                :title="`PKG B: ${row.pkg_b?.name}`"
                :column="3"
                size="mini"
                key="desc2"
                border
                :labelStyle="{ color: '#64748b', fontWeight: '700' }"
                :contentStyle="{ color: '#334155', fontWeight: '700' }">
                <el-descriptions-item label="Name">
                  {{ row.detilsB.name }}
                </el-descriptions-item>

                <el-descriptions-item label="Version">
                  {{ row.detilsB.version }}
                </el-descriptions-item>

                <el-descriptions-item label="Summary">
                  {{ row.detilsB.summary }}
                </el-descriptions-item>

                <el-descriptions-item label="Descriptions" :span="3">
                  {{ row.detilsB.desc }}
                </el-descriptions-item>

                <el-descriptions-item label="Home Page" :span="3">
                  <el-link
                    v-if="row.detilsB.homepage"
                    :underline="false"
                    :href="row.detilsB.homepage"
                    target="_blank">
                    {{ row.detilsB.homepage }}
                  </el-link>
                </el-descriptions-item>

                <el-descriptions-item label="Image">
                  {{ row.detilsB.img_name }}
                </el-descriptions-item>

                <el-descriptions-item label="Source">
                  {{ row.detilsB.source }}
                </el-descriptions-item>

                <el-descriptions-item label="Arch">
                  {{ row.detilsB.arch }}
                </el-descriptions-item>

                <el-descriptions-item label="Section Name" :span="3">
                  <div>{{ row.detilsB.section_info.name }}</div>
                </el-descriptions-item>

                <el-descriptions-item label="Relation" :span="3">
                  <div
                    v-for="(item, index) of row.detilsB.relation"
                    :key="index">
                    {{ item }}
                  </div>
                </el-descriptions-item>

                <el-descriptions-item label="Contributor" :span="3">
                  <div
                    v-for="(item, index) of row.detilsB.contributor"
                    :key="index">
                    {{ item }}
                  </div>
                </el-descriptions-item>
              </el-descriptions>
            </el-card>
          </div>
        </template>
      </el-table-column>

      <el-table-column type="index" align="center" width="50"></el-table-column>

      <el-table-column :label="`Package A (${imgA})`" header-align="center">
        <el-table-column
          prop="pkg_a"
          label="Name"
          min-width="180"
          show-overflow-tooltip>
          <template #default="{ row }">
            {{ row.pkg_a?.name }}
          </template>
        </el-table-column>

        <el-table-column
          prop="pkg_a_version"
          label="Version"
          min-width="220"
          show-overflow-tooltip></el-table-column>
      </el-table-column>

      <el-table-column
        class="package-B-header"
        :label="`Package B (${imgB})`"
        header-align="center">
        <el-table-column
          prop="pkg_b"
          label="Name"
          min-width="180"
          show-overflow-tooltip>
          <template #default="{ row }">
            {{ row.pkg_b?.name }}
          </template>
        </el-table-column>

        <el-table-column
          prop="pkg_b_version"
          label="Version"
          min-width="220"
          show-overflow-tooltip></el-table-column>
      </el-table-column>

      <el-table-column
        prop="pkg_type"
        label="Type"
        min-width="150"
        show-overflow-tooltip></el-table-column>
    </el-table>
  </div>
</template>

<script>
import {
  getComparisonTypeListAPI,
  getImageComparisonDetilsAPI,
  getPackageDetilsAPI
} from '@/services/api/image-comparison'

export default {
  name: 'ImageComparisonDetails',
  data() {
    return {
      id: this.$route.params.id,
      imgA: this.$route.query.imgA,
      imgB: this.$route.query.imgB,
      isLoadingTableData: false,
      tableData: [],
      comparisonTypeOptions: [],
      comparisonType: [],
      packageName: ''
    }
  },
  methods: {
    expandRowChange(row, expandedRows) {
      if (!row.isExpanded && expandedRows.length) {
        Promise.all([
          this.getPackageDetils(row.pkg_a?.id),
          this.getPackageDetils(row.pkg_b?.id)
        ]).then(res => {
          row.detilsA = res[0]
          row.detilsB = res[1]

          row.isExpanded = true
        })
      }
    },
    async getPackageDetils(packageId) {
      if (!packageId) return

      const { data } = await getPackageDetilsAPI(packageId)
      return data[0]
    },
    async getTableData() {
      this.isLoadingTableData = true
      const { data } = await getImageComparisonDetilsAPI(
        this.id,
        this.comparisonType,
        this.packageName
      )

      for (let i = 0; i < data.tableData.length; i++) {
        const item = data.tableData[i]
        item.index = i
        item.isExpanded = false
        item.detilsA = null
        item.detilsB = null
      }

      this.tableData = data.tableData
      this.isLoadingTableData = false
    },
    async getComparisonTypeList() {
      ;({ data: this.comparisonTypeOptions } = await getComparisonTypeListAPI())
    }
  },
  created() {
    this.getComparisonTypeList()
    this.getTableData()
  }
}
</script>

<style lang="scss" scoped>
.image-comparison-details-component {
  padding: 10px 20px;

  .title {
    text-align: center;
  }

  .expand-details-container {
    display: flex;
    padding: 20px;
    box-sizing: border-box;

    ::v-deep .el-card {
      flex: 1;
      overflow: hidden;

      .desc-a .el-descriptions__title {
        color: #16a34a;
      }

      .desc-b .el-descriptions__title {
        color: #2563eb;
      }
    }
  }
}
</style>
