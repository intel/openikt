"""The app diff application view"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import *
from .models import *
from .methods import format_resp
from django.db.models import Q
from django.core.paginator import Paginator
from .methods import email_display
from lib.ourxlsx import NewXlsx
from io import BytesIO
from django.http import HttpResponse
from lib.jenkinswrapper import JenkinsWrapper


class GetRepositoryView(APIView):
    """
    Summary
        get all rangdiff repo

    Returns:
        repo list
    """

    def get(self, request):
        """
        Returns:
            List: get quilt diff repos
        """
        repos = Repository.objects.all()
        ser = RepositorySerializers(instance=repos, many=True)
        return Response(data=format_resp(data=ser.data), status=status.HTTP_200_OK)


class GetRefsView(APIView):
    """
    Summary
        get rangediff ref_a and ref_b selector data

    Returns:
        dict include refsA/refsB
    """

    def get(self, request):
        """
        Returns:
            List: refsA and refsB
        """
        refs = RangeDiff.objects.all()
        ref_a = refs.values_list("ref_a", flat=True)
        ref_b = refs.values_list("ref_b", flat=True)
        return Response(
            data=format_resp(
                data={
                    "refsA": [{"label": a, "value": a} for a in set(ref_a)],
                    "refsB": [{"label": b, "value": b} for b in set(ref_b)],
                }
            ),
            status=status.HTTP_200_OK,
        )


class QuiltDiffView(APIView):
    """
    Summary:
        get quilt diff data api view

    Args:
        repoId: the quilt diff ref_a repo id
        diffId: the quilt diff id

    Return:
        the list of quilt diff respost data
    """

    def get(self, request):
        """
        Returns:
            Dict:
                tableData: quilt diff all tag or search table data
                tagList: for web select tag list
        """
        repoId = request.query_params.get("repoId")
        diffId = request.query_params.get("diffId")
        query = Q()
        if repoId:
            query = Q(repo_a_id=repoId) | Q(repo_b_id=repoId)
        if diffId:
            query = query & Q(id=diffId)
        diff_obj = RangeDiff.objects.select_related("repo_a", "repo_b")
        quilt_diffs = diff_obj.filter(query)
        diff_tags = diff_obj.filter(Q(repo_a_id=repoId) | Q(repo_b_id=repoId)).order_by(
            "-ref_a"
        )
        ser_tag = QulitDiffTagsSerializers(instance=diff_tags, many=True)
        ser = QulitDiffSerializers(instance=quilt_diffs, many=True)
        return Response(
            data=format_resp(data={"tableData": ser.data, "tagList": ser_tag.data}),
            status=status.HTTP_200_OK,
        )


class QuiltDiffDetailView(APIView):
    """
    Summary:
        get quilt diff detail data api view

    Args:
        quiltDIffId: the quilt diff id

    Return:
        the list of quilt diff respost data
    """

    def get(self, request):
        """
        Returns:
            Dict:
                res_patch_diff: quilt diff patch detail data
                detail: patch count
        """
        qd_id = request.query_params.get("quiltDiffId")
        qd_type = request.query_params.get("quiltDiffType")
        pagesize = request.query_params.get("pageSize", 20)
        currentpage = request.query_params.get("currentPage", 1)
        if not qd_id:
            data = format_resp(code=21001, msg="Quilt Diff Not Found")
            return Response(data=data, status=status.HTTP_404_NOT_FOUND)
        rdps = (
            RangeDiffPatch.objects.select_related("cmt_a", "cmt_b")
            .filter(rangediff_id=qd_id, patchtype=qd_type)
            .order_by("pr")
        )
        if rdps:
            ups = rdps.filter(Q(cmt_a__upstreamed_in__isnull=False) | Q(cmt_b__upstreamed_in__isnull=False))
            page_obj = Paginator(rdps, pagesize)
            page_count = page_obj.count
            page_size = page_obj.page(currentpage)
            rdps = page_size.object_list
            res_patch_diff = []
            ups_count = ups.count()
            for rdp in rdps:
                rdq_dict = {}
                commit_b = rdp.cmt_b
                ups_obj = rdp.cmt_a
                if commit_b:
                    ups_obj = commit_b
                email = ups_obj.author
                upstreamed_in = ups_obj.upstreamed_in
                if rdp.patchtype == RangeDiffPatch.TYPE_UPDATED and rdp.cmt_a:
                    rdq_dict["commit_a"] = rdp.cmt_a.commit
                    rdq_dict["git_url_cmta"] = (
                        rdp.cmt_a.repo.url() + "/commit/" + rdp.cmt_a.commit
                    )
                rdq_dict["subject"] = ups_obj.subject
                rdq_dict["pr_url"] = rdp.pr.url if rdp.pr else ""
                rdq_dict["insert_size"] = ups_obj.insert_size
                rdq_dict["delete_size"] = ups_obj.delete_size
                rdq_dict["commit"] = ups_obj.commit

                rdq_dict["upstreamedVersion"] = (
                    ups_obj.upstreamed_in if ups_obj.upstreamed_in else ""
                )
                rdq_dict["git_url"] = ups_obj.repo.url() + "/commit/" + ups_obj.commit
                rdq_dict["author"] = email_display(email)
                rdq_dict["submitter"] = email_display(email)
                if upstreamed_in:
                    rdq_dict["upstreamedVersion"] = upstreamed_in
                res_patch_diff.append(rdq_dict)
        else:
            res_patch_diff = []
            page_count = 0
            ups_count = 0
        return Response(
            data=format_resp(data=res_patch_diff, detail={"patchCount": page_count, "upsCount": ups_count}),
            status=status.HTTP_200_OK,
        )

    @staticmethod
    def getPatchDetail(ups_obj):
        """get patch detail data"""
        rdq_dict = {}
        email = ups_obj.author
        rdq_dict["subject"] = ups_obj.subject
        rdq_dict["insert_size"] = ups_obj.insert_size
        rdq_dict["delete_size"] = ups_obj.delete_size
        rdq_dict["commit"] = ups_obj.commit
        rdq_dict["upstreamedVersion"] = (
            ups_obj.upstreamed_in if ups_obj.upstreamed_in else ""
        )
        rdq_dict["git_url"] = ups_obj.repo.url() + "/commit/" + ups_obj.commit
        rdq_dict["author"] = email_display(email)
        rdq_dict["submitter"] = email_display(email)
        return rdq_dict
    
    def post(self, request, *args, **kwargs):
        qd_id = request.data.get('quiltDiffId')
        ref_a = request.data.get('refA')
        ref_b = request.data.get('refB')
        rdps = RangeDiffPatch.objects.select_related(
            'cmt_a', 'cmt_b').filter(rangediff_id=qd_id, patchtype=RangeDiffPatch.TYPE_NEW).order_by('pr')
        
        # create excel
        output = BytesIO()
        wb = NewXlsx(
            filename=output,
            options={
                # global settings
                'string_to_number': True,
                'constant_memory': False,
                'default_format_properties': {
                    'font_name': 'Calibri',
                    'font_size': 12,
                    'align': 'left',
                    'valign': 'vcenter',
                    'text_wrap': False,
                }
            }
        )
        # format cell style
        title_style = wb.add_format(
            {'bold': True,
             'font_size': 12,
             'align': 'left',
             'bg_color': '#F0F8FF',
             }
        )
        # crete sheet only A
        only_sheet_a = wb.add_worksheet(name='only ref A')
        self.write_data_excel(only_sheet_a, wb, title_style, rdps, both=False)
        
        # create sheet only b
        rdps = RangeDiffPatch.objects.select_related(
            'cmt_a', 'cmt_b').filter(rangediff_id=qd_id, patchtype=RangeDiffPatch.TYPE_REMOVED).order_by('pr')
        only_sheet_b = wb.add_worksheet(name='only ref B')
        self.write_data_excel(only_sheet_b, wb, title_style, rdps, both=False)
        
        # create both sheet
        rdps = RangeDiffPatch.objects.select_related(
            'cmt_a', 'cmt_b').filter(rangediff_id=qd_id, patchtype=RangeDiffPatch.TYPE_UPDATED).order_by('pr')
        both_sheet = wb.add_worksheet(name='both')
        self.write_data_excel(both_sheet, wb, title_style, rdps, both=True)
      
        # create same sheet
        rdps = RangeDiffPatch.objects.select_related(
            'cmt_a', 'cmt_b').filter(rangediff_id=qd_id, patchtype=RangeDiffPatch.TYPE_SAME).order_by('pr')
        if rdps:
            same_sheet = wb.add_worksheet(name='same')
            self.write_data_excel(same_sheet, wb, title_style, rdps, both=False)
        
        # create both change only sheet
        rdps = RangeDiffPatch.objects.select_related(
            'cmt_a', 'cmt_b').filter(rangediff_id=qd_id, patchtype=RangeDiffPatch.TYPE_CMCO).order_by('pr')
        if rdps:
            both_chanege_sheet = wb.add_worksheet(name='commit message change only')
            self.write_data_excel(both_chanege_sheet, wb, title_style, rdps, both=False)
        
        wb.close()
        xlsx_data = output.getvalue()
        file_name = 'Openikt quiltdiff' + '.xlsx'
        response = HttpResponse(content_type='application/ms-excel')
        response['Content-Disposition'] = 'attachment; filename={}'.format(file_name)
        response.write(xlsx_data)
        return response

    def write_data_excel(self, sheet_name, wb, title_style, rdps, both=False):
        if rdps:
            diff_sheet_tree = sheet_name.title_tree
            subject = diff_sheet_tree.add_child(
                nid='Subject',
                data=wb.get_tree_node_format_data(
                    style=title_style,
                    width=80,
                    abs_width=True
                )
            )
            if both:
                cmt_a = diff_sheet_tree.add_child(
                    nid='Commit(A)',
                    data=wb.get_tree_node_format_data(
                        style=title_style,
                        width=60
                    )
                )
                cmt_b = diff_sheet_tree.add_child(
                    nid='Commit(B)',
                    data=wb.get_tree_node_format_data(
                        style=title_style,
                        width=60
                    )
                )
            else:
                commit = diff_sheet_tree.add_child(
                    nid='Commit',
                    data=wb.get_tree_node_format_data(
                        style=title_style,
                        width=60
                    )
                )
            up_version = diff_sheet_tree.add_child(
                nid='Upstreamed Version',
                data=wb.get_tree_node_format_data(
                    style=title_style,
                    width=30
                )
            )
            pr_url = diff_sheet_tree.add_child(
                nid='Pull Request',
                data=wb.get_tree_node_format_data(
                    style=title_style,
                    width=40
                )
            )
            author = diff_sheet_tree.add_child(
                nid='Author Email',
                data=wb.get_tree_node_format_data(
                    style=title_style,
                    width=30
                )
            )
            submit = diff_sheet_tree.add_child(
                nid='Submitter Email',
                data=wb.get_tree_node_format_data(
                    style=title_style,
                    width=30
                )
            )
            size_add = diff_sheet_tree.add_child(
                nid='Size(insert)',
                data=wb.get_tree_node_format_data(
                    style=title_style,
                    width=20
                )
            )
            size_del = diff_sheet_tree.add_child(
                nid='Size(delete)',
                data=wb.get_tree_node_format_data(
                    style=title_style,
                    width=20
                )
            )
        
            for rdp in rdps:
                commit_b = rdp.cmt_b
                ups_obj = rdp.cmt_a
                if commit_b:
                    ups_obj = commit_b
                email = ups_obj.author
                subject.data['column_cells_list'].append(
                    wb.get_tree_node_format_cell(
                        value=ups_obj.subject
                    )
                )
                if both:
                    if rdp.patchtype == RangeDiffPatch.TYPE_UPDATED and rdp.cmt_a:
                        commit_a = rdp.cmt_a.commit
                    cmt_a.data['column_cells_list'].append(
                        wb.get_tree_node_format_cell(
                            value=commit_a if commit_a else ''
                        )
                    )
                    cmt_b.data['column_cells_list'].append(
                        wb.get_tree_node_format_cell(
                            value=ups_obj.commit
                        )
                    )
                else:
                    commit.data['column_cells_list'].append(
                        wb.get_tree_node_format_cell(
                            value=ups_obj.commit
                        )
                    )
                up_version.data['column_cells_list'].append(
                        wb.get_tree_node_format_cell(
                            value=ups_obj.upstreamed_in if ups_obj.upstreamed_in else ''
                        )
                    )
                pr_url.data['column_cells_list'].append(
                        wb.get_tree_node_format_cell(
                            value=rdp.pr.url if rdp.pr else ''
                        )
                    )
                author.data['column_cells_list'].append(
                        wb.get_tree_node_format_cell(
                            value=email
                        )
                    )
                submit.data['column_cells_list'].append(
                        wb.get_tree_node_format_cell(
                            value=email
                        )
                    )
                size_add.data['column_cells_list'].append(
                        wb.get_tree_node_format_cell(
                            value=ups_obj.insert_size
                        )
                    )
                size_del.data['column_cells_list'].append(
                        wb.get_tree_node_format_cell(
                            value=ups_obj.delete_size
                        )
                    )
            wb.write_worksheet(sheet_name)

class RangeDiffPatchTypeView(APIView):
    """
    Summary:
        get quilt diff patch type api view

    Return:
        the list of quilt diff patchtype data
    """

    def get(self, request):
        """get diff patch type api"""
        diffPatchType = [
            {"label": i[1], "value": i[0]} for i in RangeDiffPatch.TYPE_CHOICES
        ]
        return Response(data=format_resp(data=diffPatchType), status=status.HTTP_200_OK)


class RangeDiffTypeView(APIView):
    """
    Summary:
        get quilt diff  type api view

    Return:
        the list of quilt diff type data
    """

    def get(self, request):
        """get diff patch type api"""
        diffType = [
            {"label": i[1], "value": i[0]} for i in RangeDiff.TYPE_CHOICES
        ]
        return Response(data=format_resp(data=diffType), status=status.HTTP_200_OK)


class TriggerDiffJob(APIView):
    """
    Summary:
        trigger create diff job
    """

    @staticmethod
    def extra_repo(repo):
        protocol, rep = repo.split('://')
        first_index = rep.find('/')
        last_index = rep.rfind('/')
        host = rep[0:first_index]
        project = rep[first_index + 1:]
        name = rep[last_index + 1:]

        is_exist = Repository.objects.filter(project=project)
        if not is_exist:
            logging.info('create new repo to DB: %s' % repo)
            repo_obj = Repository.objects.create(
                protocol = protocol,
                host = host,
                project = project,
                name = name
            )
        return None

    def post(self, request, *args, **kwargs):
        form = request.data
        data = {
            'repo_url_from': form['repositoryFrom'],
            'repo_url_to': form['repositoryTo'],
            'ref_from': form['refFrom'],
            'ref_to': form['refTo'],
            'base_from': form['baseFrom'],
            'base_to': form['baseTo'],
            'diff_type': form['diffType']
        }
        self.extra_repo(form['repositoryFrom'])
        self.extra_repo(form['repositoryTo'])
        job = JenkinsWrapper(server_name='cje_jenkins')
        job.trigger_job(name='create-diff', group='OpenIKT', data=data)
        return Response(data=format_resp(data={}), status=status.HTTP_200_OK)
