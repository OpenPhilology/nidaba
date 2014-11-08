:title: Using the Iris command line util
:description: Learn how to use the Iris command line utility.

.. _using_cli:

Using the iris command line util
================================

The simplest way to put jobs into the pipeline is using the iris command line
utility. It is automatically installed during the installation procedure.

.. _cli_config:

iris config
-----------

The *config* subcommand is used to inspect the current irisconfig.py:

.. code-block:: console

        $ iris config
        * LANG_DICTS
        {u'german': (u'dicts', u'test/german.txt'),
         u'lojban': (u'dicts', u'test/lojban.txt'),
         u'polytonic_greek': (u'dicts', u'greek.dic')}
        * OCROPUS_MODELS
        {u'atlantean': (u'models', u'atlantean.pyrnn.gz'),
         u'fraktur': (u'models', u'fraktur.pyrnn.gz'),
         u'greek': (u'models', u'greek.pyrnn.gz')}
        * OLD_TESSERACT
        False
        * STORAGE_PATH
        u'~/OCR'

.. _cli_batch:

iris batch
----------

The *batch* subcommand is used to create a job for the pipeline. A rather
minimal invocation looks like this:

.. code-block:: console

        $ iris batch --binarize sauvola:10,20,30,40 --ocr tesseract:eng -- ./input.tiff
        35be45e9-9d6d-47c7-8942-2717f00f84cb

It converts the input file *input.tiff* to grayscale, binarizes it using the
Sauvola algorithm with 4 different window sizes, and finally runs it through
tesseract with the English language model.

--binarize
        Defines the binarization parameters. It consists of a list of terms in
        the format algorithm1:t1,t2,t3 algorithm2:t1,t2,... where algorithm is
        either *otsu* or *sauvola* and t1 etc. are thresholding and window size
        parameters respectively.
--ocr
        A list of OCR engine options in the format engine:lang1,lang2,lang3
        engine2:model... where engine is either *tesseract* or *ocropus* and
        lang is a tesseract language model and model is an ocropus model
        previously defined in irisconfig.
--willitblend
        Blends all output hOCR files into a single hOCR document using the
        dummy scoring algorithm.
--grayscale
        A switch to indicate that input files are already 8bpp grayscale and
        conversion to grayscale is unnecessary.

.. _cli_status:

iris status
-----------

The *status* subcommand is used to check the status of a job. It requires the
return value of the *iris batch* command.

A currently running job will return PENDING:

.. code-block:: console
        
        $ iris status 35be45e9-9d6d-47c7-8942-2717f00f84cb
        PENDING

When the job has been processed the status command will return a list of paths
containing the final output:

.. code-block:: console
        
        $ iris status 35be45e9-9d6d-47c7-8942-2717f00f84cb
        SUCCESS
                /home/mittagessen/OCR/01c00777-ea8e-46e1-bc68-95023c7d29a1/input_rgb_to_gray_binarize_sauvola_10_0.3_ocr_tesseract_eng.tiff.hocr
                /home/mittagessen/OCR/01c00777-ea8e-46e1-bc68-95023c7d29a1/input_rgb_to_gray_binarize_sauvola_20_0.3_ocr_tesseract_eng.tiff.hocr
                /home/mittagessen/OCR/01c00777-ea8e-46e1-bc68-95023c7d29a1/input_rgb_to_gray_binarize_sauvola_30_0.3_ocr_tesseract_eng.tiff.hocr
                /home/mittagessen/OCR/01c00777-ea8e-46e1-bc68-95023c7d29a1/input_rgb_to_gray_binarize_sauvola_40_0.3_ocr_tesseract_eng.tiff.hocr

Currently there is no way to detect failure of a task in a job using this
interface.
