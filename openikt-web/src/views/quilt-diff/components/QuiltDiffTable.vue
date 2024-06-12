<template>
  <div class="quilt-diff-table-component">
    <el-form :model="searchCondition" size="small" label-width="100px">
      <el-row :gutter="20">
        <el-col :span="8">
          <el-form-item label="Repository" prop="repositoryId">
            <el-select
              v-model.trim="searchCondition.repositoryId"
              placeholder="repository"
              style="width: 100%"
              clearable
              @change="handleChangeRepositorySelector">
              <el-option
                v-for="item of repositorySelectorOptions"
                :key="item.value"
                :label="item.label"
                :value="item.value"></el-option>
            </el-select>
          </el-form-item>
        </el-col>

        <el-col :span="8">
          <el-form-item label="Diff Tag" prop="diffTagId">
            <el-select
              v-model.trim="searchCondition.diffTagId"
              placeholder="diff tag (please select a repository first)"
              style="width: 100%"
              clearable
              @change="getTableData(searchCondition.repositoryId, $event)">
              <el-option
                v-for="item of diffTagSelectorOptions"
                :key="item.value"
                :label="item.label"
                :value="item.value"></el-option>
            </el-select>
          </el-form-item>
        </el-col>

        <el-col :span="8" style="text-align: right">
          <el-popconfirm
            title="Sorry, feature is under development."
            confirm-button-text="contact admin"
            cancel-button-text="cancel"
            @confirm="handleClickCreate">
            <el-button slot="reference" type="success" size="small">
              Create
            </el-button>
          </el-popconfirm>
        </el-col>
      </el-row>
    </el-form>

    <el-table
      class="ikt-table"
      :data="tableData"
      v-loading="isLoadingTableData"
      size="small"
      row-class-name="ikt-table-body-cell"
      border
      @row-click="handleClickRow">
      <el-table-column
        type="index"
        fixed
        align="center"
        width="50"></el-table-column>

      <el-table-column label="Ref A" header-align="center">
        <el-table-column
          prop="ref_a"
          label="Ref"
          min-width="220"
          show-overflow-tooltip></el-table-column>

        <el-table-column
          prop="base_a"
          label="Base Version"
          min-width="100"
          show-overflow-tooltip></el-table-column>

        <el-table-column
          prop="repoA"
          label="Repository"
          width="180"
          show-overflow-tooltip>
          <template #default="{ row }">
            <i
              v-if="row.repoA?.href"
              class="el-icon-copy-document icon-copy"
              title="copy repository url"
              @click="copyToClipboard(row.repoA?.href)"></i>

            <el-link
              v-if="row.repoA?.href"
              type="primary"
              :href="row.repoA.href"
              :underline="false"
              target="_blank"
              style="display: inline; color: inherit">
              {{ row.repoA.label }}
            </el-link>
          </template>
        </el-table-column>
      </el-table-column>

      <el-table-column label="Ref B" header-align="center">
        <el-table-column
          prop="ref_b"
          label="Ref"
          min-width="220"
          show-overflow-tooltip></el-table-column>

        <el-table-column
          prop="base_b"
          label="Base Version"
          min-width="100"
          show-overflow-tooltip></el-table-column>

        <el-table-column
          prop="repoB"
          label="Repository"
          width="180"
          show-overflow-tooltip>
          <template #default="{ row }">
            <i
              v-if="row.repoB?.href"
              class="el-icon-copy-document icon-copy"
              title="copy repository url"
              @click="copyToClipboard(row.repoB.href)"></i>

            <el-link
              v-if="row.repoB?.href"
              type="primary"
              :href="row.repoB.href"
              :underline="false"
              target="_blank"
              style="display: inline; color: inherit">
              {{ row.repoB.label }}
            </el-link>
          </template>
        </el-table-column>
      </el-table-column>

      <el-table-column
        prop="created_date"
        label="Created Date"
        header-align="center"
        align="center"
        min-width="120"
        show-overflow-tooltip></el-table-column>
    </el-table>
  </div>
</template>

<script>
import {
  getRepositoryListAPI,
  getOverviewTableDataAPI
} from '@/services/api/quilt-diff'

export default {
  name: 'QuiltDiffTable',
  data() {
    return {
      searchCondition: {
        repositoryId: '',
        diffTagId: ''
      },
      repositorySelectorOptions: [],
      diffTagSelectorOptions: [],
      tableData: [],
      isLoadingTableData: false
    }
  },
  methods: {
    async copyToClipboard(text) {
      if (!text) return

      await navigator.clipboard.writeText(text)
      this.$message({
        message: 'Copy Successfully!',
        type: 'success'
      })
    },
    parsingQuery() {
      const queryRepositoryId = +this.$route.query.repositoryId
      queryRepositoryId &&
        (this.searchCondition.repositoryId = queryRepositoryId)
      this.getTableData(queryRepositoryId)
    },
    handleClickCreate() {
      this.$router.push({ name: 'help' })
    },
    handleClickRow(row, { label }) {
      if (label === 'Repository') return

      const routeData = this.$router.resolve({
        name: 'quiltDiffDetails',
        params: {
          id: row.id
        },
        query: {
          refA: row.ref_a,
          refB: row.ref_b,
          repositoryA: row.repoA?.href,
          repositoryB: row.repoB?.href,
          type: row.diff_type,
          createdDate: row.created_date
        }
      })

      window.open(routeData.href, '_blank')
    },
    async handleChangeRepositorySelector(repositoryId) {
      this.searchCondition.diffTagId && (this.searchCondition.diffTagId = '')
      this.$router.replace({
        query: {
          repositoryId: repositoryId || undefined
        }
      })
      this.diffTagSelectorOptions = await this.getTableData(repositoryId)
    },
    async getRepositorySelectorOptions() {
      ;({ data: this.repositorySelectorOptions } = await getRepositoryListAPI())
    },
    async getTableData(repositoryId, diffTagId) {
      this.isLoadingTableData = true
      const { data } = await getOverviewTableDataAPI(repositoryId, diffTagId)
      this.tableData = data.tableData
      this.isLoadingTableData = false

      if (repositoryId && !diffTagId) {
        return data.tagList
      }
    }
  },
  async created() {
    await this.getRepositorySelectorOptions()
    this.parsingQuery()
  }
}
</script>

<style lang="scss" scoped>
.quilt-diff-table-component {
  ::v-deep .el-table {
    thead tr th {
      border-color: #cbd5e1;
    }

    .ikt-table-body-cell:hover {
      cursor: pointer;
    }

    .icon-copy {
      color: #71717a;
      cursor: pointer;

      &:hover {
        color: #2dd4bf;
      }
    }
  }
}
</style>
