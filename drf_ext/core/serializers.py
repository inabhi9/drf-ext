"""
===========
Serializers
===========
"""

from django.db.models import ForeignKey
from rest_framework import serializers as rf_serializers


class Serializer(rf_serializers.Serializer):
    """
    Base serializer that adds a feature of dynamically allow selection fields in response.
    """

    def __init__(self, *args, **kwargs):
        _fields = kwargs.pop('fields', None)
        super(Serializer, self).__init__(*args, **kwargs)

        # Dynamically allow selection of fields
        try:
            fields = self.context.get('request').GET.get('fields')
        except AttributeError:
            fields = _fields
        if fields:
            if isinstance(fields, str):
                fields = fields.split(',')
            allowed = set(fields)
            existing = set(self.fields.keys())
            for field_name in existing - allowed:
                self.fields.pop(field_name)

    @classmethod
    def subserializer_class(cls, only_fields: list = None):
        class SubSerializer(cls):
            class Meta(cls.Meta):
                fields = only_fields
                exclude = None

        return SubSerializer


class ModelSerializer(rf_serializers.ModelSerializer, Serializer):
    """
    Base serializer for model
    """

    def __init__(self, *args, **kwargs):
        super(ModelSerializer, self).__init__(*args, **kwargs)
        meta = getattr(self, 'Meta', None)

        # Update the error messages specified under the Meta class for each fields
        for field_name, err_msgs in getattr(meta, 'error_messages', {}).items():
            try:
                self.fields[field_name].error_messages.update(**err_msgs)
            except KeyError:
                pass

    @property
    def validated_data(self):
        """
        Overridden method to inject logged in user object to validated_data dict
        """
        validated_data = super(ModelSerializer, self).validated_data
        autoset_owner = getattr(self.Meta, 'autoset_owner', False)

        if getattr(self.Meta.model, 'owner', None) and autoset_owner is True:
            validated_data['owner'] = self.context['request'].user

        return validated_data

    def build_relational_field(self, field_name, relation_info):
        field_class, field_kwargs = super(ModelSerializer, self).build_relational_field(
            field_name, relation_info
        )

        # To override the queryset returned by the serializer to support enum field
        model_field = relation_info.model_field
        limit_choices_to = model_field.get_limit_choices_to()
        if isinstance(model_field, ForeignKey) and limit_choices_to:
            qs = field_kwargs.get('queryset')
            if qs:
                qs = qs.filter(**limit_choices_to)
                field_kwargs['queryset'] = qs

        return field_class, field_kwargs

    def create(self, validated_data):
        # Exclude those fields defined under Meta.exclude_on_create attribute
        exclude_on_create = getattr(self.Meta, 'exclude_on_create', [])
        for field in exclude_on_create:
            validated_data.pop(field, None)

        return super().create(validated_data)


    def update(self, instance, validated_data):
        # Exclude those fields defined under Meta.exclude_on_update attribute
        exclude_on_update = getattr(self.Meta, 'exclude_on_update', [])
        for field in exclude_on_update:
            validated_data.pop(field, None)

        return super(ModelSerializer, self).update(instance, validated_data)
