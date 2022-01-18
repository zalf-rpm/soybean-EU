#!/bin/bash -x

NODES=60
SETUPS=99367

DATE=`date +%Y-%d-%B_%H%M%S`

#calculate distribution nodes
INC=$(($SETUPS / $NODES))

NUM_LEFT=$(($SETUPS % $NODES))
if [ $NUM_LEFT -ne 0 ] ; then 
  INC=$(($INC + 1))
fi

START=0
END=0
for (( INDEX=1; INDEX<=$NODES; INDEX++ ))
do  
    START=$(($END + 1))
    END=$(($INC * $INDEX))
    echo "$START $END missing45_${INDEX}_${DATE}"
    
    BATCHID=$( sbatch --parsable jobScript_scheduler.sh $START $END missing45_${INDEX}_${DATE} )
    echo "BatchID: $BATCHID"
done
