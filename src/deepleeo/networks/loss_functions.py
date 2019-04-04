import tensorflow as tf


def twoclass_cost(predictions, labels):
    with tf.name_scope('cost'):
        predictions = tf.reshape(predictions, [-1])
        trn_labels = tf.reshape(labels, [-1])

        intersection = tf.reduce_sum(tf.multiply(predictions, trn_labels))
        union = tf.reduce_sum(tf.subtract(tf.add(predictions, trn_labels), tf.multiply(predictions, trn_labels)))
        loss = tf.subtract(tf.constant(1.0, dtype=tf.float32), tf.divide(intersection,union), name='loss')

        return loss


def avg_soft_dice(logits, labels):
    with tf.name_scope('cost'):
        epsilon = tf.constant(1e-6, dtype=tf.float32)
        intersection = tf.reduce_sum(tf.multiply(logits, labels), axis=[1, 2])
        numerator = tf.multiply(tf.constant(2., dtype=tf.float32), intersection)
        denominator = tf.reduce_sum(tf.add(tf.square(logits), tf.square(labels)), axis=[1, 2])
        dice_mean = tf.reduce_mean(tf.divide(numerator, tf.add(denominator, epsilon)))
        loss = tf.subtract(tf.constant(1., dtype=tf.float32), dice_mean, name='loss')
        # tf.add_to_collection('loss', loss)
        # loss = tf.add_n(tf.get_collection('loss'), name='loss')
        return loss


def weighted_cross_entropy(logits, labels, class_wheights, num_classes):
    with tf.name_scope('cost'):
        class_wheights = tf.reshape(class_wheights, (1, num_classes))
        weights = tf.reduce_sum(tf.multiply(labels, class_wheights), axis=1)
        loss = tf.nn.softmax_cross_entropy_with_logits(labels=labels, logits=logits)
        weighted_loss = tf.reduce_mean(weights * loss)
        return weighted_loss