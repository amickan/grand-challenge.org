import base64
import logging
from io import BytesIO
from PIL import Image

from django.conf import settings
from django.contrib.flatpages.models import FlatPage
from django.contrib.sites.models import Site
from django.core.files.base import ContentFile
from django.core.management import BaseCommand
from rest_framework.authtoken.models import Token
from userena.models import UserenaSignup
from django.contrib.auth.models import Group
from django.core.files.uploadedfile import InMemoryUploadedFile

from grandchallenge.challenges.models import (
    Challenge,
    ExternalChallenge,
    TaskType,
    BodyRegion,
    BodyStructure,
    ImagingModality,
)
from grandchallenge.evaluation.models import Result, Submission, Job, Method
from grandchallenge.pages.models import Page
import grandchallenge.algorithms.models
import grandchallenge.cases.models

logger = logging.getLogger(__name__)


def get_temporary_image():
    io = BytesIO()
    size = (200, 200)
    color = (255, 0, 0)
    image = Image.new("RGB", size, color)
    image.save(io, format="JPEG")
    image_file = InMemoryUploadedFile(
        io, None, "foo.jpg", "jpeg", image.size, None
    )
    image_file.seek(0)
    return image_file


class Command(BaseCommand):
    def handle(self, *args, **options):
        """
        Creates the main project, demo user and demo challenge
        """
        if not settings.DEBUG:
            raise RuntimeError(
                "Skipping this command, server is not in DEBUG mode."
            )

        # Set the default domain that is used in RequestFactory
        site = Site.objects.get(pk=settings.SITE_ID)

        if site.domain == "gc.localhost":
            # Already initialised
            return

        site.domain = "gc.localhost"
        site.name = "Grand Challenge"
        site.save()

        self._create_flatpages(site)

        default_users = [
            "demo",
            "demop",
            "user",
            "admin",
            "retina",
            "readerstudy",
            "workstation",
        ]
        self.users = self._create_users(usernames=default_users)

        self._set_user_permissions()
        self._create_user_tokens()
        self._create_demo_challenge()
        self._create_external_challenge()
        self._create_algorithm_demo()
        self._log_tokens()

    def _create_flatpages(self, site):
        page = FlatPage.objects.create(
            url="/about/",
            title="About",
            content="<p>You can add flatpages via django admin</p>",
        )
        page.sites.add(site)

    @staticmethod
    def _create_users(usernames):
        users = {}

        for username in usernames:
            users[username] = UserenaSignup.objects.create_user(
                username=username,
                email=f"{username}@example.com",
                password=username,
                active=True,
            )

        return users

    def _set_user_permissions(self):
        self.users["admin"].is_staff = True
        self.users["admin"].save()

        retina_group = Group.objects.get(
            name=settings.RETINA_GRADERS_GROUP_NAME
        )
        self.users["retina"].groups.add(retina_group)

        rs_group = Group.objects.get(
            name=settings.READER_STUDY_CREATORS_GROUP_NAME
        )
        self.users["readerstudy"].groups.add(rs_group)

        workstation_group = Group.objects.get(
            name=settings.WORKSTATIONS_CREATORS_GROUP_NAME
        )
        self.users["workstation"].groups.add(workstation_group)

    def _create_user_tokens(self):
        Token.objects.get_or_create(
            user=self.users["admin"],
            key="1b9436200001f2eaf57cd77db075cbb60a49a00a",
        )
        Token.objects.get_or_create(
            user=self.users["retina"],
            key="f1f98a1733c05b12118785ffd995c250fe4d90da",
        )

    def _create_demo_challenge(self):
        demo = Challenge.objects.create(
            short_name="demo",
            description="demo project",
            creator=self.users["demo"],
            use_evaluation=True,
            hidden=False,
        )
        demo.add_participant(self.users["demop"])

        Page.objects.create(challenge=demo, title="all", permission_lvl="ALL")
        Page.objects.create(challenge=demo, title="reg", permission_lvl="REG")
        Page.objects.create(challenge=demo, title="adm", permission_lvl="ADM")

        method = Method(challenge=demo, creator=self.users["demo"])
        container = ContentFile(base64.b64decode(b""))
        method.image.save("test.tar", container)
        method.save()

        submission = Submission(challenge=demo, creator=self.users["demop"])
        content = ContentFile(base64.b64decode(b""))
        submission.file.save("test.csv", content)
        submission.save()

        job = Job.objects.create(submission=submission, method=method)

        Result.objects.create(
            metrics={
                "acc": {"mean": 0.5, "std": 0.1},
                "dice": {"mean": 0.71, "std": 0.05},
            },
            job=job,
        )

        demo.evaluation_config.score_title = "Accuracy ± std"
        demo.evaluation_config.score_jsonpath = "acc.mean"
        demo.evaluation_config.score_error_jsonpath = "acc.std"
        demo.evaluation_config.extra_results_columns = [
            {
                "title": "Dice ± std",
                "path": "dice.mean",
                "error_path": "dice.std",
                "order": "desc",
            }
        ]
        demo.evaluation_config.save()

    def _create_external_challenge(self):
        ex_challenge = ExternalChallenge.objects.create(
            creator=self.users["demo"],
            homepage="https://www.example.com",
            short_name="EXAMPLE2018",
            title="Example External Challenge 2018",
            description="An example of an external challenge",
            event_name="Example Event",
            event_url="https://www.example.com/2018",
            publication_journal_name="Nature",
            publication_url="https://doi.org/10.1038/s41586-018-0367-9",
            hidden=False,
        )

        TaskType.objects.create(type="Segmentation")
        TaskType.objects.create(type="Classification")

        regions_structures = {
            "Head and Neck": ["Brain", "Teeth"],
            "Thorax": ["Lung"],
            "Cardiac": ["Heart"],
            "Abdomen": ["Liver", "Pancreas", "Kidney", "Spleen"],
            "Pelvis": ["Prostate", "Cervix"],
            "Spine": ["Spinal Cord"],
            "Upper Limb": ["Hand"],
            "Lower Limb": ["Knee"],
        }

        for region, structures in regions_structures.items():
            r = BodyRegion.objects.create(region=region)
            for structure in structures:
                BodyStructure.objects.create(structure=structure, region=r)

        modalities = (
            "CT",
            "MR",
            "XR",
            "PET",
            "PET-CT",
            "PET-MR",
            "Mammography",
            "CT-MR",
            "US",
            "TEM",
            "Histology",
        )
        for modality in modalities:
            ImagingModality.objects.create(modality=modality)

        mr_modality = ImagingModality.objects.get(modality="MR")
        ex_challenge.modalities.add(mr_modality)
        ex_challenge.save()

    def _create_algorithm_demo(self):
        cases_image = grandchallenge.cases.models.Image(
            name="test_image.mha",
            modality=ImagingModality.objects.get(modality="MR"),
            width=128,
            height=128,
            color_space="RGB",
        )
        cases_image.save()

        algorithms_algorithm = grandchallenge.algorithms.models.Algorithm(
            creator=self.users["demo"],
            title="test_algorithm",
            logo=get_temporary_image(),
        )

        container = ContentFile(base64.b64decode(b""))
        algorithms_algorithm.image.save("test_algorithm.tar", container)
        algorithms_algorithm.save()

        algorithms_job = grandchallenge.algorithms.models.Job(
            algorithm=algorithms_algorithm, image=cases_image
        )
        algorithms_job.save()

        algorithms_result = grandchallenge.algorithms.models.Result(
            output={"cancer_score": 0.5}, job=algorithms_job
        )
        algorithms_result.save()
        algorithms_result.images.add(cases_image)

    @staticmethod
    def _log_tokens():
        out = [f"\t{t.user} token is: {t}\n" for t in Token.objects.all()]
        logger.debug(f"{'*' * 80}\n{''.join(out)}{'*' * 80}")