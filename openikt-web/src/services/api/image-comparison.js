import iktRequest from '..'

export function getImageComparisonListAPI() {
  return iktRequest.get({
    url: '/openikt/app_ii/images'
  })
}

export function getImageComparisonTableDataAPI(imageComparisonId) {
  return iktRequest.get({
    url: '/openikt/app_ii/image_list',
    params: {
      imageId: imageComparisonId || undefined
    }
  })
}

export function getImageListAPI() {
  return iktRequest.get({
    url: '/openikt/app_ii/image_data'
  })
}

export function getOSListAPI() {
  return iktRequest.get({
    url: '/openikt/app_ii/os_list'
  })
}

export function verifyCreateImageExistAPI(imageAName, imageBName) {
  return iktRequest.get({
    url: `/openikt/app_ii/diff_exist?imgA=${imageAName}&imgB=${imageBName}`
  })
}

export function verifyCreateImageNameAPI(imageName) {
  return iktRequest.get({
    url: `/openikt/app_ii/name_verify?name=${imageName}`
  })
}

export function verifyCreateImageUrlAPI(imageUrl) {
  return iktRequest.get({
    url: `/openikt/app_ii/url_verify?url=${imageUrl}`
  })
}

export function createImageComparisonAPI(data) {
  return iktRequest.post({
    url: '/openikt/app_ii/create',
    data
  })
}

export function getPackageTypeListAPI() {
  return iktRequest.get({
    url: '/openikt/app_ii/pkg_type'
  })
}

export function getImageComparisonDetilsAPI(
  imageComparisonId,
  packageType,
  packageName
) {
  return iktRequest.get({
    url: `/openikt/app_ii/image_diff_pkg?DiffId=${imageComparisonId}`,
    params: {
      diffType: packageType?.toString() || undefined,
      packageName: packageName || undefined
    }
  })
}

export function getPackageDetilsAPI(packageId) {
  return iktRequest.get({
    url: `/openikt/app_ii/pkg_detail?PackageId=${packageId}`
  })
}
