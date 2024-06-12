<template>
  <div class="quilt-diff-details-components">
    <h2 class="title">Quilt Diff Details</h2>

    <i class="back-btn el-icon-back" @click="handleBack"></i>

    <el-row>
      <el-col :span="20">
        <h3 style="margin-top: 0">
          {{ mainTag }}
          <i
            class="iconfont icon-business-icon-vs"
            style="
              color: #4f46e5;
              font-size: 36px;
              position: relative;
              top: 5px;
            "></i>
          {{ previousTag }}
        </h3>
      </el-col>

      <el-col :span="4">
        <text-button-export @handle-export="handleExport"></text-button-export>
      </el-col>

      <el-col>
        <el-descriptions :column="2" size="mini" :colon="false">
          <el-descriptions-item
            :span="2"
            :content-style="{
              'flex-direction': 'column'
            }">
            <template slot="label">
              <i
                class="iconfont icon-git-repository-line"
                style="color: #3b82f6"></i>
            </template>

            <el-link
              v-if="repositoryA"
              type="primary"
              :href="repositoryA"
              :underline="false"
              target="_blank">
              <span style="color: #020617">ref A</span>
              {{ repositoryA }}
            </el-link>

            <el-link
              v-if="repositoryB"
              type="primary"
              :href="repositoryB"
              :underline="false"
              target="_blank">
              <span style="color: #020617">ref B</span>
              {{ repositoryB }}
            </el-link>
          </el-descriptions-item>

          <el-descriptions-item>
            <template slot="label">
              <i class="iconfont icon-type" style="color: #a3e635"></i>
            </template>
            {{ $route.query.type }}
          </el-descriptions-item>

          <el-descriptions-item>
            <template slot="label">
              <i class="iconfont icon-e-date-build" style="color: #67e8f9"></i>
            </template>
            {{ $route.query.createdDate }}
          </el-descriptions-item>
        </el-descriptions>
      </el-col>
    </el-row>

    <div
      v-for="(item, index) of tableList"
      :key="item.value"
      v-show="item.data.length">
      <h4>
        {{ getTableTitle(item.value, mainTag, previousTag) }}
        <span>
          <span title="total">
            <i
              class="iconfont icon-shujutongji"
              style="color: #4ade80; margin: 0 5px 0 10px"></i>
            <span style="color: #1e40af">{{ item.total }}&nbsp;</span>
          </span>

          <span>(&nbsp;upstreamed:&nbsp;</span>
          <span style="color: #1e40af">{{ item.upstreamedTotal }}</span>
          <span>, no upstreamed:</span>
          <span style="color: #1e40af">
            {{ item.total - item.upstreamedTotal }}
          </span>
          <span>)</span>
        </span>
      </h4>

      <el-table
        class="ikt-table"
        :data="item.data"
        v-loading="item.isLoading"
        max-height="300px"
        size="small"
        border>
        <el-table-column
          type="index"
          fixed
          align="center"
          width="50"></el-table-column>

        <el-table-column
          prop="subject"
          label="Subject"
          min-width="300px"
          show-overflow-tooltip>
          <template #default="{ row }">
            <el-link
              type="primary"
              :href="row.git_url"
              :underline="false"
              target="_blank"
              style="display: inline; color: #606266">
              {{ row.subject }}
            </el-link>
          </template>
        </el-table-column>

        <el-table-column
          v-if="item.value === 2"
          prop="commit"
          label="Commit(A)"
          min-width="150px"
          show-overflow-tooltip>
          <template #default="{ row }">
            <el-link
              type="primary"
              :href="row.git_url_cmta"
              :underline="false"
              target="_blank"
              style="display: inline; color: #606266">
              {{ row.commit_a }}
            </el-link>
          </template>
        </el-table-column>

        <el-table-column
          prop="commit"
          :label="item.value !== 2 ? 'Commit' : 'Commit(B)'"
          min-width="150px"
          show-overflow-tooltip>
          <template #default="{ row }">
            <el-link
              type="primary"
              :href="row.git_url"
              :underline="false"
              target="_blank"
              style="display: inline; color: #606266">
              {{ row.commit }}
            </el-link>
          </template>
        </el-table-column>

        <el-table-column
          prop="upstreamedVersion"
          label="Upstreamed Version"
          width="170px"
          sortable></el-table-column>

        <el-table-column
          prop="pr_url"
          label="Pull Request"
          width="100px"
          show-overflow-tooltip>
          <template #default="{ row }">
            <el-link
              v-if="row.pr_url"
              type="primary"
              :href="row.pr_url"
              :underline="false"
              target="_blank"
              style="display: inline">
              {{ '#' + row.pr_url.split('pulls/')[1] }}
            </el-link>
          </template>
        </el-table-column>

        <el-table-column
          prop="author"
          label="Author Email"
          width="180px"
          show-overflow-tooltip>
          <template #default="{ row }">
            <div class="people-container">
              <el-avatar
                :style="{ backgroundColor: row.author[1] }"
                size="small">
                {{ extractNameInitials(row.author[0]) }}
              </el-avatar>
              <span class="username">{{ row.author[2] }}</span>
            </div>
          </template>
        </el-table-column>

        <el-table-column
          prop="submitter"
          label="Submitter Email"
          width="180px"
          show-overflow-tooltip>
          <template #default="{ row }">
            <div class="people-container">
              <el-avatar
                :style="{ backgroundColor: row.submitter[1] }"
                size="small">
                {{ extractNameInitials(row.submitter[0]) }}
              </el-avatar>
              <span class="username">{{ row.submitter[2] }}</span>
            </div>
          </template>
        </el-table-column>

        <el-table-column prop="insert_size" label="Size" width="80px">
          <template #default="{ row }">
            <compare-code-size
              :code-size="{
                deleteSize: row.delete_size,
                addSize: row.insert_size
              }"></compare-code-size>
          </template>
        </el-table-column>
      </el-table>

      <el-pagination
        class="ikt-table-pagination"
        :disabled="item.isLoading"
        :current-page="item.page.currentPage"
        :page-size="item.page.pageSize"
        :page-sizes="[10, 20, 30, 100, 500]"
        :total="item.total"
        layout="total, sizes, prev, pager, next, jumper"
        @size-change="handleSizeChange(index, $event)"
        @current-change="handleCurrentChange(index, $event)"></el-pagination>
    </div>
  </div>
</template>

<script>
import TextButtonExport from '@/components/export'
import CompareCodeSize from '@/components/comparison'

import { extractNameInitials } from '@/utils'

import {
  getDetailsTableDataAPI,
  getBinaryExportDataAPI
} from '@/services/api/quilt-diff'

export default {
  name: 'QuiltDiffDetails',
  components: {
    TextButtonExport,
    CompareCodeSize
  },
  data() {
    return {
      mainTag: this.$route.query.refA,
      previousTag: this.$route.query.refB,
      repositoryA: this.$route.query.repositoryA,
      repositoryB: this.$route.query.repositoryB,
      tableData: null,
      tableList: [
        {
          label: 'new',
          value: 1,
          data: [],
          isLoading: false,
          page: {
            currentPage: 1,
            pageSize: 20
          },
          total: 0,
          upstreamedTotal: 0
        },
        {
          label: 'removed',
          value: 3,
          data: [],
          isLoading: false,
          page: {
            currentPage: 1,
            pageSize: 20
          },
          total: 0,
          upstreamedTotal: 0
        },
        {
          label: 'updated',
          value: 2,
          data: [],
          isLoading: false,
          page: {
            currentPage: 1,
            pageSize: 20
          },
          total: 0,
          upstreamedTotal: 0
        },
        {
          label: 'same',
          value: 5,
          data: [],
          isLoading: false,
          page: {
            currentPage: 1,
            pageSize: 20
          },
          total: 0,
          upstreamedTotal: 0
        },
        {
          label: 'cmtmsg changed only',
          value: 4,
          data: [],
          isLoading: false,
          page: {
            currentPage: 1,
            pageSize: 20
          },
          total: 0,
          upstreamedTotal: 0
        }
      ]
    }
  },
  methods: {
    extractNameInitials,
    async handleExport(cb) {
      const { excelData, excelFilename } = await getBinaryExportDataAPI({
        quiltDiffId: +this.$route.params.id,
        refA: this.mainTag,
        refB: this.previousTag
      })
      cb(excelData, excelFilename)
    },
    getTableTitle(typeId, mainTag, previousTag) {
      switch (typeId) {
        case 1:
          return `Only in ${previousTag}`
        case 2:
          return `In both ${mainTag} and ${previousTag}`
        case 3:
          return `Only in ${mainTag}`
        case 4:
          return `In both ${mainTag} and ${previousTag} commit message change only`
        case 5:
          return 'Same'
        default:
          return ''
      }
    },
    handleSizeChange(tableIndex, pageSize) {
      this.tableList[tableIndex].page = {
        currentPage: 1,
        pageSize
      }
      this.getTableData(tableIndex)
    },
    handleCurrentChange(tableIndex, currentPage) {
      this.tableList[tableIndex].page.currentPage = currentPage
      this.getTableData(tableIndex)
    },
    handleBack() {
      this.$router.push({
        name: 'quiltDiff'
      })
    },
    async getTableData(tableIndex) {
      const table = this.tableList[tableIndex]
      table.isLoading = true
      const { data, detail } = await getDetailsTableDataAPI(
        this.$route.params.id,
        table.value,
        table.page
      )
      table.data = data
      table.total = detail.patchCount
      table.upstreamedTotal = detail.upsCount
      this.tableList[tableIndex].isLoading = false
    },
    getAllTableFirstPageData() {
      for (const index of this.tableList.keys()) {
        this.getTableData(index)
      }
    }
  },
  created() {
    this.getAllTableFirstPageData()
  }
}
</script>

<style lang="scss" scoped>
.quilt-diff-details-components {
  padding: 10px 20px;
  position: relative;

  .back-btn {
    position: absolute;
    top: 10px;
    left: 20px;
    font-size: 26px;
    color: #409eff;
    cursor: pointer;

    &:hover {
      color: #38bdf8;
    }
  }

  .title {
    text-align: center;
  }

  ::v-deep .el-descriptions__body {
    background-color: transparent;
  }

  .people-container {
    display: inline-flex;
    align-items: center;

    .username {
      padding-left: 10px;
    }
  }

  ::v-deep .el-avatar {
    width: 20px;
    height: 20px;
    line-height: 20px;
    font-size: 10px;
  }

  ::v-deep .ikt-table-pagination.el-pagination {
    margin-top: 15px;
    text-align: right;

    & > button,
    .el-pager > .number,
    .el-pager > .more {
      background-color: transparent;
    }

    .el-pager > .number:hover {
      border-radius: 20px;
      color: #334155;
      background: #e5e7eb;
    }
  }
}
</style>
