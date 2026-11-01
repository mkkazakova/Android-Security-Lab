package org.example.securitylab.owner

import android.content.ContentProvider
import android.content.ContentValues
import android.database.Cursor
import android.database.MatrixCursor
import android.net.Uri

abstract class ReadOnlyTestProvider : ContentProvider() {
    override fun onCreate(): Boolean = true

    override fun query(
        uri: Uri,
        projection: Array<out String>?,
        selection: String?,
        selectionArgs: Array<out String>?,
        sortOrder: String?
    ): Cursor {
        val value = context!!.openFileInput("secret.txt").bufferedReader().use { it.readText() }
        return MatrixCursor(arrayOf("value")).apply { addRow(arrayOf(value)) }
    }

    override fun getType(uri: Uri): String = "vnd.android.cursor.item/vnd.securitylab.sample"
    override fun insert(uri: Uri, values: ContentValues?): Uri? = null
    override fun delete(uri: Uri, selection: String?, selectionArgs: Array<out String>?): Int = 0
    override fun update(uri: Uri, values: ContentValues?, selection: String?, selectionArgs: Array<out String>?): Int = 0
}

class PrivateProvider : ReadOnlyTestProvider()
class PublicProvider : ReadOnlyTestProvider()
class ProtectedProvider : ReadOnlyTestProvider()
