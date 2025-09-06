from django.test import TestCase
from django.core.exceptions import ValidationError
from ..minacce.models import Minaccia
from ..controlli.models import Controllo
from .models import ElementType, ValoreElementType
from ..campagne.models import Campagna # Assuming Campagna is needed for ElementType

class ElementTypeValidationTest(TestCase):

    def setUp(self):
        self.campagna = Campagna.objects.create(nome="Test Campagna", descrizione="Descrizione test")
        self.element_type = ElementType.objects.create(
            nome="Test ElementType",
            campagna=self.campagna,
            is_base=True,
            is_enabled=False
        )

        # Create threats
        self.threat1 = Minaccia.objects.create(nome="Threat 1", descrizione="Desc 1", campagna=self.campagna)
        self.threat2 = Minaccia.objects.create(nome="Threat 2", descrizione="Desc 2", campagna=self.campagna)

        # Create controls
        self.control_p1 = Controllo.objects.create(nome="Control P1", descrizione="Desc P1", tipologia_controllo="Tecnologico", categoria_controllo="preventive", campagna=self.campagna)
        self.control_p2 = Controllo.objects.create(nome="Control P2", descrizione="Desc P2", tipologia_controllo="Tecnologico", categoria_controllo="preventive", campagna=self.campagna)
        self.control_p3 = Controllo.objects.create(nome="Control P3", descrizione="Desc P3", tipologia_controllo="Tecnologico", categoria_controllo="preventive", campagna=self.campagna)
        self.control_d1 = Controllo.objects.create(nome="Control D1", descrizione="Desc D1", tipologia_controllo="Tecnologico", categoria_controllo="detective", campagna=self.campagna)
        self.control_d2 = Controllo.objects.create(nome="Control D2", descrizione="Desc D2", tipologia_controllo="Tecnologico", categoria_controllo="detective", campagna=self.campagna)
        self.control_d3 = Controllo.objects.create(nome="Control D3", descrizione="Desc D3", tipologia_controllo="Tecnologico", categoria_controllo="detective", campagna=self.campagna)
        self.control_other = Controllo.objects.create(nome="Control Other", descrizione="Desc Other", tipologia_controllo="Documentale", categoria_controllo="preventive", campagna=self.campagna)


    def test_enable_with_no_threats(self):
        """Test that ElementType cannot be enabled if it has no associated threats."""
        self.element_type.minacce.clear() # Remove any default threats if any
        self.element_type.is_enabled = True
        with self.assertRaisesMessage(ValidationError, "L'ElementType non può essere abilitato perché non ha minacce associate (righe della matrice)."):
            self.element_type.full_clean()

    def test_enable_threat_missing_preventive_controls(self):
        """Test that ElementType cannot be enabled if a threat lacks 2 preventive controls."""
        self.element_type.minacce.add(self.threat1)
        self.element_type.minacce.add(self.threat2)

        # Threat 1 has 1 preventive, 2 detective
        ValoreElementType.objects.create(elementtype=self.element_type, minaccia=self.threat1, controllo=self.control_p1, valore=1.0)
        ValoreElementType.objects.create(elementtype=self.element_type, minaccia=self.threat1, controllo=self.control_d1, valore=1.0)
        ValoreElementType.objects.create(elementtype=self.element_type, minaccia=self.threat1, controllo=self.control_d2, valore=1.0)

        # Threat 2 has enough controls
        ValoreElementType.objects.create(elementtype=self.element_type, minaccia=self.threat2, controllo=self.control_p1, valore=1.0)
        ValoreElementType.objects.create(elementtype=self.element_type, minaccia=self.threat2, controllo=self.control_p2, valore=1.0)
        ValoreElementType.objects.create(elementtype=self.element_type, minaccia=self.threat2, controllo=self.control_d1, valore=1.0)
        ValoreElementType.objects.create(elementtype=self.element_type, minaccia=self.threat2, controllo=self.control_d2, valore=1.0)

        self.element_type.is_enabled = True
        with self.assertRaisesMessage(ValidationError, f"La minaccia '{self.threat1.nome}' non ha almeno 2 controlli preventivi e 2 controlli detective associati a questo ElementType."):
            self.element_type.full_clean()

    def test_enable_threat_missing_detective_controls(self):
        """Test that ElementType cannot be enabled if a threat lacks 2 detective controls."""
        self.element_type.minacce.add(self.threat1)
        self.element_type.minacce.add(self.threat2)

        # Threat 1 has 2 preventive, 1 detective
        ValoreElementType.objects.create(elementtype=self.element_type, minaccia=self.threat1, controllo=self.control_p1, valore=1.0)
        ValoreElementType.objects.create(elementtype=self.element_type, minaccia=self.threat1, controllo=self.control_p2, valore=1.0)
        ValoreElementType.objects.create(elementtype=self.element_type, minaccia=self.threat1, controllo=self.control_d1, valore=1.0)

        # Threat 2 has enough controls
        ValoreElementType.objects.create(elementtype=self.element_type, minaccia=self.threat2, controllo=self.control_p1, valore=1.0)
        ValoreElementType.objects.create(elementtype=self.element_type, minaccia=self.threat2, controllo=self.control_p2, valore=1.0)
        ValoreElementType.objects.create(elementtype=self.element_type, minaccia=self.threat2, controllo=self.control_d1, valore=1.0)
        ValoreElementType.objects.create(elementtype=self.element_type, minaccia=self.threat2, controllo=self.control_d2, valore=1.0)

        self.element_type.is_enabled = True
        with self.assertRaisesMessage(ValidationError, f"La minaccia '{self.threat1.nome}' non ha almeno 2 controlli preventivi e 2 controlli detective associati a questo ElementType."):
            self.element_type.full_clean()

    def test_enable_control_not_associated_with_any_threat(self):
        """Test that ElementType cannot be enabled if a control assigned to it is not in the matrix."""
        self.element_type.minacce.add(self.threat1)
        self.element_type.minacce.add(self.threat2)

        # Assign controls to element_type (this is done via the ForeignKey in Controllo model)
        # This simulates controls that are "assigned" to the element type but not necessarily in the matrix
        self.control_p1.elementtype = self.element_type
        self.control_p1.save()
        self.control_p2.elementtype = self.element_type
        self.control_p2.save()
        self.control_d1.elementtype = self.element_type
        self.control_d1.save()
        self.control_d2.elementtype = self.element_type
        self.control_d2.save()
        self.control_other.elementtype = self.element_type # This control is assigned but not in matrix
        self.control_other.save()

        # Threat 1 has enough controls
        ValoreElementType.objects.create(elementtype=self.element_type, minaccia=self.threat1, controllo=self.control_p1, valore=1.0)
        ValoreElementType.objects.create(elementtype=self.element_type, minaccia=self.threat1, controllo=self.control_p2, valore=1.0)
        ValoreElementType.objects.create(elementtype=self.element_type, minaccia=self.threat1, controllo=self.control_d1, valore=1.0)
        ValoreElementType.objects.create(elementtype=self.element_type, minaccia=self.threat1, controllo=self.control_d2, valore=1.0)

        self.element_type.is_enabled = True
        with self.assertRaisesMessage(ValidationError, f"L'ElementType non può essere abilitato perché i seguenti controlli assegnati non sono presenti nella matrice di rischio (non associati a nessuna minaccia): \"{self.control_other.nome}\"."):
            self.element_type.full_clean()

    def test_enable_threat_without_any_controls_in_matrix(self):
        """Test that ElementType cannot be enabled if a threat has no controls in the matrix."""
        self.element_type.minacce.add(self.threat1)
        self.element_type.minacce.add(self.threat2)

        # Threat 1 has enough controls
        ValoreElementType.objects.create(elementtype=self.element_type, minaccia=self.threat1, controllo=self.control_p1, valore=1.0)
        ValoreElementType.objects.create(elementtype=self.element_type, minaccia=self.threat1, controllo=self.control_p2, valore=1.0)
        ValoreElementType.objects.create(elementtype=self.element_type, minaccia=self.threat1, controllo=self.control_d1, valore=1.0)
        ValoreElementType.objects.create(elementtype=self.element_type, minaccia=self.threat1, controllo=self.control_d2, valore=1.0)

        # Threat 2 is associated but has no ValoreElementType entries
        self.element_type.is_enabled = True
        with self.assertRaisesMessage(ValidationError, f"L'ElementType non può essere abilitato perché le seguenti minacce (righe) non hanno nessun controllo associato nella matrice: \"{self.threat2.nome}\"."):
            self.element_type.full_clean()

    def test_enable_success(self):
        """Test that ElementType can be enabled when all criteria are met."""
        self.element_type.minacce.add(self.threat1)
        self.element_type.minacce.add(self.threat2)

        # Threat 1: 2 preventive, 2 detective
        ValoreElementType.objects.create(elementtype=self.element_type, minaccia=self.threat1, controllo=self.control_p1, valore=1.0)
        ValoreElementType.objects.create(elementtype=self.element_type, minaccia=self.threat1, controllo=self.control_p2, valore=1.0)
        ValoreElementType.objects.create(elementtype=self.element_type, minaccia=self.threat1, controllo=self.control_d1, valore=1.0)
        ValoreElementType.objects.create(elementtype=self.element_type, minaccia=self.threat1, controllo=self.control_d2, valore=1.0)

        # Threat 2: 2 preventive, 2 detective
        ValoreElementType.objects.create(elementtype=self.element_type, minaccia=self.threat2, controllo=self.control_p1, valore=1.0)
        ValoreElementType.objects.create(elementtype=self.element_type, minaccia=self.threat2, controllo=self.control_p3, valore=1.0) # Using p3 for variety
        ValoreElementType.objects.create(elementtype=self.element_type, minaccia=self.threat2, controllo=self.control_d1, valore=1.0)
        ValoreElementType.objects.create(elementtype=self.element_type, minaccia=self.threat2, controllo=self.control_d3, valore=1.0) # Using d3 for variety

        # Ensure all controls assigned to element_type are in the matrix
        self.control_p1.elementtype = self.element_type
        self.control_p1.save()
        self.control_p2.elementtype = self.element_type
        self.control_p2.save()
        self.control_p3.elementtype = self.element_type
        self.control_p3.save()
        self.control_d1.elementtype = self.element_type
        self.control_d1.save()
        self.control_d2.elementtype = self.element_type
        self.control_d2.save()
        self.control_d3.elementtype = self.element_type
        self.control_d3.save()

        self.element_type.is_enabled = True
        try:
            self.element_type.full_clean()
        except ValidationError as e:
            self.fail(f"ValidationError unexpectedly raised: {e.message_dict}")
        
        # If full_clean passes, save the instance to ensure it works
        self.element_type.save()
        self.assertTrue(self.element_type.is_enabled)
