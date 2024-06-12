import iktRequest from '../..'

export function getRepositoryListAPI() {
  return iktRequest.get({
    url: '/openikt/app_diff/repos'
  })
}

export function getOverviewTableDataAPI(repositoryId, diffTagId) {
  return iktRequest.get({
    url: '/openikt/app_diff/quilt_diffs',
    params: {
      repoId: repositoryId || undefined,
      diffId: diffTagId || undefined
    }
  })
}

export function getDetailsTableDataAPI(quiltDiffId, quiltDiffType, page) {
  return iktRequest.get({
    url: '/openikt/app_diff/detail',
    params: {
      quiltDiffId: quiltDiffId,
      quiltDiffType: quiltDiffType,
      currentPage: page?.currentPage || 1,
      pageSize: page?.pageSize || 20
    }
  })
}

export function getBinaryExportDataAPI(data) {
  return iktRequest.post({
    url: '/openikt/app_diff/detail',
    responseType: 'arraybuffer',
    data,
    interceptors: {
      responseInterceptor(res) {
        res.data = {
          excelData: res.data,
          excelFilename:
            res.headers['content-disposition'].split('filename=')[1]
        }
        return res
      }
    }
  })
}
