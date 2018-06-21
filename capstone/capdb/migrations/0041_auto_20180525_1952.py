# Generated by Django 2.0.2 on 2018-05-25 19:52

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('capdb', '0040_auto_20180525_1905'),
    ]

    operations = [
        # update the `size` column in our xml tables.
        # drop the `versioning_trigger` trigger during this update -- we don't need copies without size populated.
        # the versioning trigger will be recreated after migrations by `set_up_postgres`, which is called by `fab migrate`.
        migrations.RunSQL(
            """
                DROP TRIGGER IF EXISTS versioning_trigger ON {table};
                UPDATE {table} SET size=octet_length(text(orig_xml)) WHERE size IS null;
            """.format(table="capdb_"+model_name),
            migrations.RunSQL.noop
        )
        for model_name in ['volumexml', 'pagexml', 'casexml', 'volumexml_history', 'pagexml_history', 'casexml_history']
    ]